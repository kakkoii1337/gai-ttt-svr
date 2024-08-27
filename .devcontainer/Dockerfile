# syntax=docker/dockerfile:1.2
FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda

# devcontainer Options
ARG INSTALL_ZSH="true"
ARG UPGRADE_PACKAGES="false"
ARG USERNAME=kakkoii1337
ARG USER_UID=1000
ARG USER_GID=$USER_UID
COPY .devcontainer/library-scripts/*.sh .devcontainer/library-scripts/*.env /tmp/library-scripts/

# Install system deps and poetry
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
    # Install common packages, non-root user
    && bash /tmp/library-scripts/common-debian.sh "${INSTALL_ZSH}" "${USERNAME}" "${USER_UID}" "${USER_GID}" "${UPGRADE_PACKAGES}" "true" "true" \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Setup default python tools in a venv via pipx to avoid conflicts
ENV PIPX_HOME=/usr/local/py-utils \
    PIPX_BIN_DIR=/usr/local/py-utils/bin
ENV PATH=${PATH}:${PIPX_BIN_DIR}
RUN if [ ! -e /usr/local/bin/python3 ]; then ln -s /opt/conda/bin/python3 /usr/local/bin/python3; fi
RUN bash /tmp/library-scripts/python-debian.sh "none" "/usr/local" "${PIPX_HOME}" "${USERNAME}" \ 
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN echo Switching to non-root user $USERNAME
USER $USERNAME

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
ARG HOME_PATH="/home/$USERNAME"
RUN curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Create and activate virtual environment
RUN python -m venv ${HOME_PATH}/venv \
    # disable virtual env management by poetry
    && poetry config virtualenvs.create false

# enable source
SHELL ["/bin/bash","-c"]
ENV PATH="${HOME_PATH}/venv/bin/python:${PATH}"

# Set "CACHEBUST" from devcontainer.json to rebuild from here if needed
ARG CACHEBUST=1
ENV CACHEBUST=${CACHEBUST}

#Install dependencies(773s)
ENV CACHE_PATH=${HOME_PATH}/.cache/pypoetry
RUN --mount=type=cache,target=${CACHE_PATH} \
    source ${HOME_PATH}/venv/bin/activate \
    && pip install "torch==2.2.0" \
    && pip install "numpy==1.26.4" \
    && if [ ! -f "${HOME}/.cache/pypoetry/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" ]; then \
         wget "https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" -P ${HOME}/.cache/pypoetry; \
        fi \
        && pip install "${HOME}/.cache/pypoetry/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl"

# Create .gairc
RUN echo "{\"app_dir\":\"${HOME_PATH}/.gai\"}" > ${HOME_PATH}/.gairc && mkdir -p ${HOME_PATH}/.gai

# Prepare ~/.gai
ENV MODEL_PATH="${HOME_PATH}/.gai/models"
ENV CATEGORY="ttt"
VOLUME ${HOME_PATH}/.gai

COPY .devcontainer/postCreateCommand.sh ${HOME_PATH}/postCreateCommand.sh