FROM kakkoii1337/gai_torch2.2.0_cuda12.1_ubuntu22.04_devcontainer:1.0.25 AS build


FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# devcontainer Options
# ---
# Environment variables
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ENV PYTHON_VERSION=${PYTHON_VERSION}

# Install system deps
RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update  \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends \
        sudo \
        git \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
        wget \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
ENV HOME_PATH="/root"
ENV PACKAGES_PATH="${HOME_PATH}/.venv/lib/${PYTHON_VERSION}/site-packages"
ENV DOWNLOAD_PATH="${HOME_PATH}/downloads"
ARG CACHEBUST=1    

# Install Python deps
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
        setuptools \
        wheel \
        build \
        notebook \
        jupyterlab \
        ipywidgets \
        pytest \
        nest-asyncio

# syntax=docker/dockerfile:1.2
FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Setup virtual env
RUN python -m venv ${HOME_PATH}/.venv
SHELL ["/bin/bash","-c"]
ENV PATH="${HOME_PATH}/.venv/bin:${PATH}"

# Install
ENV WHEEL_FILE="${DOWNLOAD_PATH}/llama_cpp_python-0.2.90-cp310-cp310-linux_x86_64.whl"
COPY --from=build ${PACKAGES_PATH} ${PACKAGES_PATH}
COPY --from=build ${WHEEL_FILE} ${WHEEL_FILE} 
RUN pip install --no-cache-dir --no-deps --no-index --find-links ${PACKAGES_PATH} ${DOWNLOAD_PATH}/llama_cpp_python-0.2.90-cp310-cp310-linux_x86_64.whl

# Create .gairc
RUN echo "{\"app_dir\":\"${HOME_PATH}/.gai\"}" > ${HOME_PATH}/.gairc && mkdir -p ${HOME_PATH}/.gai

# Prepare ~/.gai
ENV MODEL_PATH="${HOME_PATH}/.gai/models"
ENV CATEGORY="ttt"
VOLUME ${HOME_PATH}/.gai
WORKDIR /workspaces/gai-ttt-svr/src/gai/ttt/server/api
COPY startup.sh .
CMD ["bash","startup.sh"]