from dataclasses import dataclass, field
import os, sys, platform, subprocess, psutil, logging
from typing import Optional, Tuple, Union, Dict, List
import torch

@dataclass
class WhisperXConfig:
    model_size: str
    device: str
    compute_type: str
    batch_size: int
    device_index: int = 0
    threads: int = 4

    # Metadata for debugging/logging, very useful
    _reason: dict = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict:
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "batch_size": self.batch_size,
            "device_index": self.device_index,
            "threads": self.threads,
        }

    def explain(self) -> str:
        lines = ["WhisperX Config Rationale:"]
        for k, v in self._reason.items():
            lines.append(f"  {k}: {v}")
            
        return "\n".join(lines)


def _get_cuda_info() -> tuple[bool, Optional[int], Optional[str]]:
    """
    Returns (cuda_available, vram_mb, gpu_name).
    Tries torch first, falls back to nvidia-smi.
    """

    # Try PyTorch first...
    try:
        import torch

        if torch.cuda.is_available():
            idx = torch.cuda.current_device()
            vram = torch.cuda.get_device_properties(idx).total_memory // (1024**2)
            name = torch.cuda.get_device_name(idx)
            return True, vram, name

    except ImportError:
        # not handling here, just letting execution continue and return False etc
        pass

    # Fallback: trying nvidia-smi...
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,name",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            vram = int(parts[0].strip())
            name = parts[1].strip() if len(parts) > 1 else "Unknown GPU"
            return True, vram, name

    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
        # not worrying about these exceptions here, just letting execution continue and return False etc
        pass

    return False, None, None


def _get_ram_gb() -> float:
    return psutil.virtual_memory().total / (1024**3)


def _get_cpu_cores() -> int:
    return (
        psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 2
    )  # cascading fallback to default of 2 cores


def _supports_float16_cpu() -> bool:
    """Check if CPU supports float16 via AVX2 (rough heuristic)."""

    try:
        import subprocess

        if platform.system() == "Linux":
            result = subprocess.run(
                ["grep", "-m1", "avx2", "/proc/cpuinfo"], capture_output=True, text=True
            )
            return "avx2" in result.stdout
        
        elif platform.system() == "Darwin":
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.features"], capture_output=True, text=True
            )
            
            return "AVX2" in result.stdout

    except Exception as e:
        # not handling here, just letting execution continue and return False etc
        pass

    return False


def auto_configure_whisperx(
    prefer_accuracy: bool = True,
    prefer_speed: bool = False,
    verbose: bool = False,
) -> WhisperXConfig:
    """
    Attempts to automatically determine optimal WhisperX configuration based on current system specs.

    Args:
        prefer_accuracy: Bias toward larger models even at cost of speed.
        prefer_speed:    Bias toward smaller models / faster compute types.
        verbose:         Print rationale to stdout. (highly suggested)

    Returns:
        WhisperXConfig dataclass with recommended default WhisperX model settings based on system specs.
    """

    reasons = {}

    # ── Hardware detection ───────────────────────────────────────────────────
    cuda_available, vram_mb, gpu_name = _get_cuda_info()
    ram_gb = _get_ram_gb()
    cpu_cores = _get_cpu_cores()
    cpu_float16 = _supports_float16_cpu()

    reasons["ram_gb"] = f"{ram_gb:.1f} GB"
    reasons["cpu_cores"] = cpu_cores
    reasons["cuda"] = (
        f"{cuda_available} ({gpu_name}, {vram_mb} MB VRAM)"
        if cuda_available
        else "not available"
    )

    # ── Device ───────────────────────────────────────────────────────────────
    if cuda_available and vram_mb is not None and vram_mb >= 2048:
        device = "cuda"
        reasons["device"] = "CUDA selected (GPU detected with sufficient VRAM)"
    else:
        device = "cpu"
        reasons["device"] = "CPU selected (no CUDA or insufficient VRAM)"

    # ── Model size ───────────────────────────────────────────────────────────
    # Reference:
    # Approximate VRAM / RAM requirements per model:
    #   tiny   ~1 GB   large-v2 ~10 GB
    #   base   ~1 GB   large-v3 ~10 GB
    #   small  ~2 GB   turbo    ~6 GB
    #   medium ~5 GB
    if device == "cuda":
        resource = vram_mb / 1024  # GB
        resource_label = f"{resource:.1f} GB VRAM"
    else:
        resource = ram_gb
        resource_label = f"{resource:.1f} GB RAM"

    # Apply bias modifiers
    bias = 1 if prefer_accuracy else (-1 if prefer_speed else 0)

    model_tiers = [
        (1.5, "tiny"),
        (2.5, "base"),
        (4.0, "small"),
        (7.0, "medium"),
        (11.0, "large-v2"),
        (
            float("inf"),
            "large-v3",
        ),  # for anything above the 11.0 threshold, use large-v3
    ]

    chosen_model = "tiny"
    for threshold, name in model_tiers:
        if resource >= threshold:
            chosen_model = name

    # Apply bias: shift one tier up or down
    model_names = [m for _, m in model_tiers]
    idx = model_names.index(chosen_model)
    idx = max(0, min(len(model_names) - 1, idx + bias))
    chosen_model = model_names[idx]

    reasons["model_size"] = f"{chosen_model} (based on {resource_label})"

    # ── Compute type ─────────────────────────────────────────────────────────
    if device == "cuda":
        # float16 is standard on modern NVIDIA; use int8 only on very low VRAM
        if vram_mb >= 4096:
            compute_type = "float16"
            reasons["compute_type"] = "float16 (CUDA, ≥4 GB VRAM)"
        else:
            compute_type = "int8_float16"
            reasons["compute_type"] = "int8_float16 (CUDA, limited VRAM)"
    else:
        # CPU: int8 is fastest and well-supported; float16 rarely beneficial on CPU
        if prefer_accuracy and cpu_float16:
            compute_type = "float32"
            reasons["compute_type"] = "float32 (CPU, accuracy mode, AVX2 present)"
        else:
            compute_type = "int8"
            reasons["compute_type"] = "int8 (CPU default — best speed/memory tradeoff)"

    # ── Batch size ───────────────────────────────────────────────────────────
    if device == "cuda":
        if vram_mb >= 10000:
            batch_size = 32
        elif vram_mb >= 6000:
            batch_size = 16
        elif vram_mb >= 4000:
            batch_size = 8
        else:
            batch_size = 4
    else:
        # CPU batch sizing based on RAM and cores
        if ram_gb >= 32 and cpu_cores >= 8:
            batch_size = 8
        elif ram_gb >= 16 and cpu_cores >= 4:
            batch_size = 4
        else:
            batch_size = 2

    if prefer_speed:
        batch_size = min(batch_size * 2, 64)
        reasons["batch_size"] = f"{batch_size} (speed-biased, doubled)"
    elif prefer_accuracy:
        batch_size = max(batch_size // 2, 1)
        reasons["batch_size"] = f"{batch_size} (accuracy-biased, halved)"
    else:
        reasons["batch_size"] = str(batch_size)

    # ── CPU threads ──────────────────────────────────────────────────────────
    # WhisperX passes this to faster-whisper / CTranslate2
    threads = max(2, min(cpu_cores, 8))  # cap at 8; diminishing returns beyond that
    reasons["threads"] = f"{threads} (of {cpu_cores} physical cores)"

    # ── Build config ─────────────────────────────────────────────────────────
    config = WhisperXConfig(
        model_size=chosen_model,
        device=device,
        compute_type=compute_type,
        batch_size=batch_size,
        device_index=0,
        threads=threads,
        _reason=reasons,
    )

    if verbose:
        logging.info(config.explain())

    return config
