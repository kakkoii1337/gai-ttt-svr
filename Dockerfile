# syntax=docker/dockerfile:1.2

FROM kakkoii1337/torch2.2.0-cuda12.1-ubuntu22.04-base:latest as build


# Build Final ----------------------------------------------------------------------------------------

FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime AS base
ARG CATEGORY=ttt
ARG DEVICE=cuda
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1

# Step 1: Install poetry
RUN apt update && apt install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt remove -y curl \
    && apt autoremove -y \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:${PATH}"
RUN poetry config virtualenvs.create false

## Step 2: Install exllamav2
RUN pip install https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl

# Step 3: Copy Source Code
WORKDIR /app
COPY src/gai/ttt src/gai/ttt
COPY pyproject.toml.docker ./pyproject.toml
RUN poetry install

# Step 5: Startup
RUN echo '{"app_dir":"/app/.gai"}' > /root/.gairc
VOLUME /app/.gai
ENV MODEL_PATH="/app/.gai/models"
ENV CATEGORY=${CATEGORY}
WORKDIR /app/src/gai/ttt/server/api
CMD ["bash","-c","python main.py"]

