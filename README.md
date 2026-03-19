# AudioNotetaker

A transcription and audio note-taking application with local LLM summarization.

> **Note:** The initial/first run of the app requires network access.

---

## Prerequisites

- [Git](https://git-scm.com/) with credential manager or browser login for auth
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full-shared.7z) — use the `--full-shared` build (verify with `ffmpeg -version`)
- A [Hugging Face](https://huggingface.co/) account with an access token
- Python 3.12+

---

## Installation

### 1. Clone the Repository

Start in an empty directory, for example a `projects` folder in your home directory:

```bash
cd ~ && mkdir projects && cd projects
git clone --depth=1 https://github.com/verdande2/STAT405_AudioNotetaker.git
cd STAT405_AudioNotetaker
```

---

### 2. Configure Environment Variables

In a text editor or IDE, open (or create) a `.env` file in the project root. Use `.env.example` as a template. The key variables are:

```env
HF_TOKEN=INSERT_HUGGING_FACE_TOKEN_HERE       # Required — your Hugging Face access token
HF_HUB_DISABLE_SYMLINKS_WARNING=true          # Disables symlink warnings from HF Hub
INPUT_DEFAULT_LANGUAGE=None                   # None = auto-detect; or use ISO 639-1 code e.g. "en"
CACHED_MODEL_DIR=models_cache/                # Cache dir for whisperx and related models
HF_DATASETS_CACHE=hf_datasets_cache/         # For testing data only — can be ignored
```

To generate your `HF_TOKEN`:

1. Go to [HF Access Tokens](https://huggingface.co/settings/tokens)
2. Click **+ Create new token**
3. Give it any name — default settings are fine
4. Click **Create Token**, then **Copy**
5. Paste the token as the value for `HF_TOKEN=` in your `.env` file

---

### 3. Download the Summarizer Model

1. Download the model file from [Google Drive](https://drive.google.com/file/d/1Qj5Q-HucBemO2ZG_jBj1t9sp-wVT-vCn/view)
2. In the project root, create a `/models/` directory:
   ```bash
   mkdir models
   ```
   > This folder is excluded by `.gitignore` — you must create it manually each time you clone.
3. Place the downloaded model file inside `/models/`

---

### 4. Install ffmpeg

Download the [ffmpeg full-shared build for Windows](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full-shared.7z), extract it, and add its `bin/` directory to your system `PATH`.

If you're unsure about PATH configuration, you can place the extracted ffmpeg folder directly in the project root as a fallback.

Verify your install:

```bash
ffmpeg -version
```

---

### 5. Install Dependencies

In the project root, run:

```bash
uv sync --extra local-llm
```

> This may take a while — the final package in particular is large.

---

### 6. Bootstrap the App

Run the following one-time setup script:

```bash
uv run python scripts/create_psychologist.py --use-master-admin-password
```

---

## Running the App

From the project root:

```bash
uv run python main.py
```

**Admin password:** `STAT405_ADMIN`

---

## Debugging in VSCode

1. Open the project in VSCode
2. Select the correct Python interpreter:
   - Press `Ctrl+Shift+P` → type `interpreter` → select **Python: Select Interpreter**
   - Choose `Python 3.12.12 (projectname) .\.venv\Scripts\python.exe` (should appear as recommended)
3. Open `main.py`
4. Press **F5** → select **Active Python File**

---

## Quick Reference

| Step | Command |
|------|---------|
| Clone repo | `git clone --depth=1 https://github.com/verdande2/STAT405_AudioNotetaker.git` |
| Install deps | `uv sync --extra local-llm` |
| Bootstrap | `uv run python scripts/create_psychologist.py --use-master-admin-password` |
| Run app | `uv run python main.py` |
| Admin password | `STAT405_ADMIN` |