# syntax=docker/dockerfile:1.2
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime AS base
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda
ENV PATH="/usr/local/cuda-12.1/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/cuda-12.1/lib64:/usr/lib/wsl/lib:$LD_LIBRARY_PATH"

#Step 1: Install deps and poetry
RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends \
        wget \
        curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt remove -y curl \
    && apt autoremove -y \
    && apt clean \    
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:${PATH}"
RUN poetry config virtualenvs.create false

# Step 2: Install exllamav2
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ ! -f /root/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl ]; then \
        wget https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl -P /root/.cache/pip; \
    fi \
    && pip install /root/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl

# Step 3: Copy Source Code
WORKDIR /app
COPY src/gai/ttt src/gai/ttt
COPY pyproject.toml poetry.lock ./
RUN poetry export --output=requirements.txt

# Step 4: Install gai-ttt-svr
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install  --disable-pip-version-check --no-deps --requirement=/app/requirements.txt --only-binary :all:

# Step 5: Install project
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-interaction --no-ansi -vv

# Step 6: Startup
RUN echo '{"app_dir":"/app/.gai"}' > /root/.gairc
VOLUME /app/.gai
ENV MODEL_PATH="/app/.gai/models"
ENV CATEGORY=${CATEGORY}
WORKDIR /app/src/gai/ttt/server/api

# Step 7: Create get_version.sh script
RUN echo '#!/bin/bash' > /app/src/gai/ttt/server/api/get_version.sh && \
    echo "python -c \"import toml; print(toml.load('/app/pyproject.toml')['tool']['poetry']['version'])\"" >> /app/src/gai/ttt/server/api/get_version.sh && \
    chmod +x /app/src/gai/ttt/server/api/get_version.sh

CMD ["bash", "-c", "./get_version.sh; echo 'Starting main.py...'; python main.py"]

