#!/usr/bin/env python3
"""Build helper for TranscribeNotes PyInstaller packaging.

Performs pre-flight checks then invokes PyInstaller with the project spec.

Usage (from the repo root, inside a Python 3.12 venv):
    python packaging/build.py
    python packaging/build.py --clean     # wipe dist/ and build/ first
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = REPO_ROOT / "packaging" / "TranscribeNotes.spec"
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"
MODELS_DIR = REPO_ROOT / "models"

REQUIRED_PYTHON = (3, 12)


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

def check_python_version() -> bool:
    v = sys.version_info
    if (v.major, v.minor) != REQUIRED_PYTHON:
        print(
            f"[ERROR] Python {v.major}.{v.minor} detected.\n"
            f"        PyInstaller requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}.\n"
            "        Create and activate a Python 3.12 virtual environment, then re-run:\n"
            "          py -3.12 -m venv .venv-build\n"
            "          .venv-build\\Scripts\\activate        # Windows\n"
            "          source .venv-build/bin/activate     # macOS\n"
            "          pip install -e '.[local-llm]'\n"
            "          pip install pyinstaller\n"
        )
        return False
    print(f"[OK] Python {v.major}.{v.minor}")
    return True


def check_pyinstaller() -> bool:
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
        return True
    except ImportError:
        print(
            "[ERROR] PyInstaller not found.\n"
            "        Install it in your build environment:  pip install pyinstaller"
        )
        return False


def check_model_file() -> bool:
    """Require at least one .gguf model in models/."""
    # Also accept the file at the repo root (common mistake) and suggest the fix.
    root_gguf = list(REPO_ROOT.glob("*.gguf"))
    models_gguf = list(MODELS_DIR.glob("*.gguf"))

    if not models_gguf:
        msg = (
            f"[ERROR] No .gguf model found in {MODELS_DIR}/\n"
            "        The model must live in the models/ subdirectory so that the\n"
            "        bundled app can locate it at runtime.\n"
        )
        if root_gguf:
            names = ", ".join(f.name for f in root_gguf)
            msg += (
                f"        Found {names} at the repo root — move it:\n"
                f"          mkdir models\n"
                f"          mv {root_gguf[0].name} models/\n"
            )
        print(msg)
        return False

    for f in models_gguf:
        size_gb = f.stat().st_size / (1024 ** 3)
        print(f"[OK] Model: {f.name}  ({size_gb:.2f} GB)")
    return True


def check_dependencies() -> bool:
    """Spot-check that key packages are importable."""
    packages = {
        "PySide6":                  "pyside6",
        "sqlcipher3":               "sqlcipher3",
        "llama_cpp":                "llama-cpp-python  (run: pip install -e '.[local-llm]')",
        "langchain_text_splitters": "langchain-text-splitters",
    }
    ok = True
    for module, install_hint in packages.items():
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError:
            print(f"[ERROR] Cannot import '{module}'.  Install: {install_hint}")
            ok = False
    return ok


# ---------------------------------------------------------------------------
# Build helpers
# ---------------------------------------------------------------------------

def clean_build_artifacts() -> None:
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            print(f"[CLEAN] Removing {d}")
            shutil.rmtree(d)


def run_pyinstaller() -> None:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC_FILE),
        "--noconfirm",
    ]
    print(f"\n[BUILD] {' '.join(cmd)}\n{'=' * 60}\n")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print("\n[ERROR] PyInstaller exited with errors (see output above).")
        sys.exit(result.returncode)

    out_dir = DIST_DIR / "TranscribeNotes"
    print(
        f"\n[DONE] Build succeeded.\n"
        f"       Output folder: {out_dir}\n"
        f"\n"
        f"       To deploy, copy the entire '{out_dir.name}' folder to a USB drive.\n"
        f"       The end user launches:  TranscribeNotes.exe  (Windows)\n"
        f"                                TranscribeNotes      (macOS)\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the TranscribeNotes standalone distributable."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove dist/ and build/ directories before building.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  TranscribeNotes — PyInstaller Build Pre-flight")
    print("=" * 60 + "\n")

    checks = [
        check_python_version(),
        check_pyinstaller(),
        check_dependencies(),
        check_model_file(),
    ]

    if not all(checks):
        print("\n[ABORT] Fix the errors above before building.\n")
        sys.exit(1)

    print("\n[OK] All pre-flight checks passed.\n")

    if args.clean:
        clean_build_artifacts()

    run_pyinstaller()


if __name__ == "__main__":
    main()
