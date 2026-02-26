# ============================================================
# Stage 1 — Build FFmpeg (x264 + NVENC)
# ============================================================
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS ffmpeg-builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    pkg-config \
    yasm \
    nasm \
    autoconf \
    automake \
    libtool \
    cmake \
    ca-certificates \
    libx264-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone --depth 1 https://github.com/FFmpeg/nv-codec-headers.git \
    && cd nv-codec-headers \
    && make && make install

RUN git clone --depth 1 https://git.ffmpeg.org/ffmpeg.git ffmpeg \
    && cd ffmpeg \
    && ./configure \
        --prefix=/usr/local \
        --enable-gpl \
        --enable-nonfree \
        --enable-libx264 \
        --enable-nvenc \
        --enable-cuda-nvcc \
        --enable-shared \
        --disable-static \
        --disable-debug \
        --disable-doc \
        --enable-ffmpeg \
        --enable-ffprobe \
    && make -j$(nproc) \
    && make install \
    && strip /usr/local/bin/ffmpeg \
    && strip /usr/local/bin/ffprobe


# ============================================================
# Stage 2 — Runtime
# ============================================================
FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:64
ENV OMP_NUM_THREADS=4

WORKDIR /app
ARG DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# Runtime dependencies
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxrender1 \
    libavcodec59 \
    libavformat59 \
    libavutil57 \
    libswresample4 \
    libx264-164 \
    libsndfile1 \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy FFmpeg
COPY --from=ffmpeg-builder /usr/local/bin/ffmpeg /usr/local/bin/
COPY --from=ffmpeg-builder /usr/local/bin/ffprobe /usr/local/bin/
COPY --from=ffmpeg-builder /usr/local/lib /usr/local/lib
RUN ldconfig

# ------------------------------------------------------------
# Install uv
# ------------------------------------------------------------
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ------------------------------------------------------------
# Install CUDA Torch (works on CPU too)
# Using cu121 for best compatibility
# ------------------------------------------------------------
RUN uv pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cu121 \
    torch torchvision torchaudio

# ------------------------------------------------------------
# Install project deps including pyannote + whisperx
# ------------------------------------------------------------
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-cache

# ------------------------------------------------------------
# Copy project
# ------------------------------------------------------------
COPY . .

CMD ["uv", "run", "python", "main.py"]