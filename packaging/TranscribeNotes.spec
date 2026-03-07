# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for TranscribeNotes (Windows and macOS, CPU-only).

Prerequisites — see packaging/README_DEPLOY.md for the full walkthrough:
  - Python 3.12 build environment (PyInstaller does NOT support Python 3.14)
  - PyInstaller >= 6.0 installed in that environment
  - All project dependencies installed:  pip install -e ".[local-llm]"
  - GGUF model file placed at:          <repo_root>/models/Qwen3-4B-Q5_0.gguf

Build command (run from the repo root):
  pyinstaller packaging/TranscribeNotes.spec --noconfirm
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# ---------------------------------------------------------------------------
# Paths — SPECPATH is the directory containing this .spec file (packaging/)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(SPECPATH).parent
MODELS_DIR = REPO_ROOT / "models"

# ---------------------------------------------------------------------------
# Guard: GGUF model must be present at build time
# ---------------------------------------------------------------------------
GGUF_FILES = list(MODELS_DIR.glob("*.gguf"))
if not GGUF_FILES:
    raise FileNotFoundError(
        f"\n[BUILD ERROR] No .gguf model found in {MODELS_DIR}/\n"
        "  Move the model file into the models/ directory before building:\n"
        "    mkdir models\n"
        "    mv Qwen3-4B-Q5_0.gguf models/\n"
    )

# ---------------------------------------------------------------------------
# Collect all datas / binaries / hidden-imports for heavy packages
# ---------------------------------------------------------------------------
pyside6_datas,   pyside6_bins,   pyside6_hidden   = collect_all("PySide6")
llama_datas,     llama_bins,     llama_hidden     = collect_all("llama_cpp")
langchain_datas, langchain_bins, langchain_hidden = collect_all("langchain_text_splitters")
sqlcipher_datas, sqlcipher_bins, sqlcipher_hidden = collect_all("sqlcipher3")

# ---------------------------------------------------------------------------
# Data files bundled into the package
# ---------------------------------------------------------------------------
datas = [
    # GGUF model(s) — placed under models/ inside the bundle so that
    # Summarizer.py's Path(__file__).parents[2] / "models" resolution works.
    *[(str(f), "models") for f in GGUF_FILES],

    # Placeholder transcript used by the stub transcription stage.
    # placeholder_transcript.py resolves via Path(__file__).parents[2] / "sample_data"
    (str(REPO_ROOT / "sample_data"), "sample_data"),

    # Sample JSON docs used by the LM testing utilities
    (str(REPO_ROOT / "app" / "lm" / "testing"), "app/lm/testing"),

    # Package-collected datas
    *pyside6_datas,
    *langchain_datas,
    *llama_datas,
    *sqlcipher_datas,
]

# ---------------------------------------------------------------------------
# Native binaries (DLLs / dylibs)
# ---------------------------------------------------------------------------
binaries = [
    *pyside6_bins,
    *llama_bins,
    *sqlcipher_bins,
]

# ---------------------------------------------------------------------------
# Hidden imports — modules that PyInstaller cannot detect via static analysis
# ---------------------------------------------------------------------------
hiddenimports = [
    # Heavy collected packages
    *pyside6_hidden,
    *llama_hidden,
    *langchain_hidden,
    *sqlcipher_hidden,

    # sqlcipher3 loads its dbapi2 extension dynamically
    "sqlcipher3",
    "sqlcipher3.dbapi2",

    # Windows key-store uses ctypes.windll at import time (conditional block)
    "ctypes",
    "ctypes.wintypes",

    # All application modules — listed explicitly so PyInstaller does not miss
    # anything loaded via string-based imports or conditional try/except blocks.
    "app",
    "app.db",
    "app.db.database",
    "app.db.auth",
    "app.db.records",
    "app.lm",
    "app.lm.Summarizer",
    "app.pages",
    "app.pages.dashboard",
    "app.pages.upload",
    "app.pages.patients",
    "app.pages.patient_detail",
    "app.pages.transcripts",
    "app.pages.accounts",
    "app.pages.settings",
    "app.pages.login",
    "app.security",
    "app.security.key_store",
    "app.services",
    "app.services.session_processing",
    "app.services.placeholder_transcript",
    "app.src",
    "app.src.AudioTranscriber.AudioTranscriber",
    "app.src.ProjectSettings.ProjectSettings",
    "app.src.TranscriptTranslator.TranscriptTranslator",
    "app.components",
    "app.components.no_scroll_combo",
    "app.styles",
    "app.main_window",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(REPO_ROOT / "main.py")],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    # Custom hooks directory (e.g. hook-sqlcipher3.py)
    hookspath=[str(REPO_ROOT / "packaging" / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude GPU/CUDA libraries — CPU-only build
        "torch",
        "torchaudio",
        "torchvision",
        "nvidia",
        # Exclude transcribe-anything and its heavy ML stack.
        # These are installed as dependencies but are not yet imported
        # by any code path in the application.
        "transcribe_anything",
        "faster_whisper",
        "pyannote",
        "whisper",
        # Exclude unused tooling
        "mlflow",
        "pytest",
        "matplotlib",
        "notebook",
        "IPython",
        "ipykernel",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # Required for onedir (COLLECT) mode
    name="TranscribeNotes",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                  # UPX can corrupt Qt and llama_cpp binaries
    console=False,              # Windowed GUI — no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                  # TODO: supply a .ico (Windows) / .icns (macOS)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TranscribeNotes",
)
