FROM kakkoii1337/torch2.2.0-cuda12.1-ubuntu22.04-base:latest as build
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1

# Install system deps
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt update && apt upgrade -y && apt install -y --no-install-recommends \
        sudo \
        git \
        curl

# Install python deps
RUN pip install --upgrade \
    pip \
    setuptools \
    wheel \
    build \
    notebook \
    jupyterlab \
    ipywidgets \
    ipykernel \
    pytest \
    nest-asyncio

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN ~/.local/bin/poetry config virtualenvs.create false
ENV PATH="~/.local/bin:${PATH}"

## Install exllamav2
RUN pip install https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
    
# Configure Gai
ENV MODEL_PATH="/root/.gai/models"
ENV CATEGORY="itt"
RUN echo '{"app_dir":"/root/.gai"}' > /root/.gairc
VOLUME /root/.gai


