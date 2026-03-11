import torch, torchcodec, platform, subprocess

print(f"torch version: {torch.__version__}",
      f"torchcodec version: {torchcodec.__version__}",
      f"local python version: {platform.python_version()}"
      )

subprocess.run(["ffmpeg","-version"], check = True)