# TranscribeNotes — Build and Deployment Guide

This document covers how to build a standalone distributable and deploy it to
an air-gapped machine via USB drive.

---

## Overview

The application is packaged with **PyInstaller** into a self-contained folder.
No Python installation, pip, or internet access is required on the target machine.

```
TranscribeNotes/          ← copy this entire folder to USB
├── TranscribeNotes.exe   ← launch this (Windows)
├── TranscribeNotes       ← launch this (macOS)
└── _internal/            ← all dependencies, models, data (do not modify)
```

---

## Build Machine Requirements

| Requirement | Detail |
|---|---|
| OS | Windows 10+ (for Windows build) / macOS 12+ (for macOS build) |
| Python | **3.12** — PyInstaller does not support Python 3.14 |
| Internet | Required only on the **build** machine, not the target |
| Disk space | ~8 GB free (model + PyInstaller output) |

> Each platform must be built on its own OS. A Windows build cannot be produced
> on macOS and vice versa.

---

## Step 1 — Prepare the model file

The GGUF model must be in the `models/` subdirectory of the repo root before
building. If the file is currently at the repo root, move it:

```bash
mkdir models
mv Qwen3-4B-Q5_0.gguf models/
```

Verify:
```
repo_root/
└── models/
    └── Qwen3-4B-Q5_0.gguf   (~3.5 GB)
```

---

## Step 2 — Create a Python 3.12 build environment

The project's default `.python-version` targets Python 3.14, which PyInstaller
does not yet support. Create a **separate** build environment using Python 3.12.

### Windows

```cmd
py -3.12 -m venv .venv-build
.venv-build\Scripts\activate
```

### macOS

```bash
python3.12 -m venv .venv-build
source .venv-build/bin/activate
```

> If Python 3.12 is not installed, download it from python.org or use
> `pyenv install 3.12`.

---

## Step 3 — Install dependencies

Inside the activated `.venv-build` environment, install the project and all
required extras, plus PyInstaller:

```bash
pip install -e ".[local-llm]"
pip install pyinstaller
```

> `transcribe-anything` and `torch` are listed in the project dependencies but
> are not yet integrated into the application code. PyInstaller will exclude
> them automatically via the `excludes` list in the spec file, keeping the
> bundle size manageable.

---

## Step 4 — Run the build

From the **repo root** with `.venv-build` activated:

```bash
python packaging/build.py
```

The script runs pre-flight checks (Python version, missing model, missing
packages) before invoking PyInstaller. To wipe previous build artifacts first:

```bash
python packaging/build.py --clean
```

On success, the distributable is at:

```
dist/TranscribeNotes/
```

Build time is typically 3–10 minutes depending on hardware.

---

## Step 5 — Copy to USB drive

Copy the entire `dist/TranscribeNotes/` folder to the USB drive.

```
USB:\
└── TranscribeNotes\
    ├── TranscribeNotes.exe
    └── _internal\
        └── ...
```

Do **not** copy only the `.exe` — the `_internal/` folder is required.

---

## Step 6 — Running on the target machine

1. Plug the USB drive into the target machine.
2. Copy `TranscribeNotes\` from the USB to a local folder (e.g., Desktop or
   `C:\Programs\TranscribeNotes\`). Running directly from USB is slower.
3. Launch `TranscribeNotes.exe`.
4. On first launch, the app will:
   - Generate and persist an AES-256 database encryption key via Windows DPAPI
     (stored in `%LOCALAPPDATA%\TranscribeNotes\db_key.bin`).
   - Create the encrypted database at
     `%LOCALAPPDATA%\TranscribeNotes\data\transcribenotes.db`.
   - Present the login screen — run the admin bootstrap script first (see below).

No internet connection, Python installation, or admin rights are required.

---

## First-time admin setup (target machine)

Before any user can log in, an admin account must be created. From the USB
drive (or a copy of the repo), run the bootstrap script using the bundled
Python or any available Python 3.12+:

```bash
# If the build environment is still available on the build machine,
# run this before packaging and export the DB, OR use the included
# scripts/ folder:
python scripts/bootstrap_admin.py
```

Alternatively, implement a first-run setup wizard in the GUI (recommended for
the final product).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError: No .gguf model` at build | Model not in `models/` | See Step 1 |
| `ModuleNotFoundError: llama_cpp` at build | Missing `--extra local-llm` | Re-run `pip install -e ".[local-llm]"` |
| App crashes on launch (Windows) — missing DLL | sqlcipher3 native lib not collected | Ensure `sqlcipher3` installed in `.venv-build`; re-run build |
| Summarizer returns "model not found" at runtime | GGUF not bundled or wrong path | Confirm model is in `models/` at build time |
| App launches but DB fails to open | Key store inaccessible | Check `%LOCALAPPDATA%\TranscribeNotes\` exists and is writable |
| Black window / no GUI on macOS | Qt platform plugin missing | Ensure PySide6 fully collected; check `_internal/PySide6/` |

---

## Known limitations

- **macOS code signing**: The bundle is unsigned. macOS Gatekeeper will block
  it on first run. The user must right-click → Open, or the build machine must
  apply an Apple Developer signature (`codesign_identity` in the spec file).
- **Python 3.14 incompatibility**: The project's default environment uses
  Python 3.14. The packaging build must use a separate Python 3.12 venv.
  This can be eliminated once PyInstaller adds Python 3.14 support.
- **`transcribe-anything` (STT) not yet bundled**: The speech-to-text stage
  currently uses a placeholder. When it is integrated, the `excludes` list in
  `TranscribeNotes.spec` must be updated to include `faster_whisper` and
  pre-downloaded Whisper model weights must be added to `datas`.
