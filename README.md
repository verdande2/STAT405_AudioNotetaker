# AudioNotetaker Project


## Installation Quickstart
Initial/first run of app requires network access!




1. Start in empty directory. Ex. new folder `projects` in your home dir:

`cd ~ && mkdir projects && cd projects`

2. Use Git credential manager/browser login/whatever needed to auth and shallow clone the whole repository to `~/projects`:

`cd ~/projects && git clone --depth=1 https://github.com/verdande2/STAT405_AudioNotetaker.git`

1. In a text editor or IDE, open/create as needed the `.env` file in the project root. The `.env.example` file has the template for the variables. The main one that is "secret" and not committed to the repo is the `HF_TOKEN`, which is used to download the HF gated models on first run. The `.env` vars relevant to the transcription/translation/diarization/alignment are:

```
HF_TOKEN=INSERT_HUGGING_FACE_TOKEN_HERE # the only really important one that needs to be set, 

HF_HUB_DISABLE_SYMLINKS_WARNING = true # disable symlink feature of HF_HUB (not needed for this project)

INPUT_DEFAULT_LANGUAGE=None # leave as None to auto-detect, otherwise =  2-char ISO 639-1 language code, ie. "en", etc

CACHED_MODEL_DIR=models_cache/ # cache dir for models from whisperx and the like, set to anywhere you have read/write/execute permissions

HF_DATASETS_CACHE = hf_datasets_cache/ # datasets cache dir for TESTING data only, ignore
```

1. Open browser, open: [HF Access Tokens](https://huggingface.co/settings/tokens) -> Click  `+ Create new token` button to the right -> set `Token name` to whatever, not important -> defaults should all be fine for general fine-grained token settings -> click `Create Token` button at the bottom -> click `Copy` button to the right of the token name -> set `HF_TOKEN=` the copied HF Access Token oin your local project_root's `.env` file.




1. While the repo clones, in git bash or similar, while in the project root, run:
`uv sync`

1. Quick and dirty bootstrapping:
`uv run python scripts/create_psychologist.py --use-master-admin-password`

1. Install the ffmpeg build linked ([here for windows](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full-shared.7z), ensure it is the build ran with the `--full-shared` flag, check `ffmpeg -version` to confirm proper version/build), extract it locally somewhere, and ensure that you have the bin directory set in your sys.PATH. If in doubt, dump ffmpeg folder and all its contents as is in the project root.


## DEBUG
1. In VSCode, make sure you have proper the proper venv python interpreter selected. Ctrl-Shift-P -> type "interpreter" -> select "Python: Select Interpreter" -> select "Python 3.12.12 (projectname) .\.venv\Scripts\python.exe" (should be recommended)

2. Open the `main.py` file, press **F5** to start debugging -> select "Active Python File"


## To run program from CLI:\
1. In project_root, run:
`uv run python main.py`

1.
1.
1.
