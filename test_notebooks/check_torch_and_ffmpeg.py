import torch, torchcodec, platform, subprocess

print("torch", torch.__version__, "torchcodec", torchcodec.__version__, "py", platform.python_version())

subprocess.run(["ffmpeg","-version"], check=True)