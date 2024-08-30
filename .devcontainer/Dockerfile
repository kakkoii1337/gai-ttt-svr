# syntax=docker/dockerfile:1.2
FROM python:3.10-bullseye

# devcontainer Options
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ARG INSTALL_ZSH="true"
ARG UPGRADE_PACKAGES="false"
ARG USERNAME=kakkoii1337
ARG USER_UID=1000
ARG USER_GID=$USER_UID
COPY ./library-scripts/*.sh ./library-scripts/*.env /tmp/library-scripts/

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
ARG HOME_PATH="/home/$USERNAME"

#-------------------------------------------------
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda
ENV MODEL_PATH="${HOME_PATH}/.ollama/models"    

# Install ollama
RUN curl -fsSL https://ollama.com/install.sh | sh
RUN mkdir ${HOME_PATH}/.ollama

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && "${HOME_PATH}/.local/bin/poetry" config virtualenvs.create false
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Create and activate virtual environment
RUN python -m venv ${HOME_PATH}/.venv \
    && echo "source ~/.venv/bin/activate" >> ~/.bashrc

# enable source
SHELL ["/bin/bash","-c"]
ENV PATH="${HOME_PATH}/.venv/bin/python:${PATH}"

# Install python deps
RUN --mount=type=cache,target=${CACHE_PATH} \
    source ${HOME_PATH}/.venv/bin/activate \
    && pip install --upgrade \
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

#-------------------------------------------------
COPY ./postCreateCommand.sh ${HOME_PATH}/postCreateCommand.sh

