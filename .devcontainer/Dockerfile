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
COPY library-scripts/*.sh library-scripts/*.env /tmp/library-scripts/

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
ENV HOME_PATH="/home/$USERNAME"
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    # enable virtual environment to allow non-root user to install packages in container
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

# Step 2: Install exllamav2
RUN --mount=type=cache,target=${HOME_PATH}/.cache/pip \
    if [ ! -f ${HOME_PATH}/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl ]; then \
        wget https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl -P ${HOME_PATH}/.cache/pip; \
    fi \
    && pip install ${HOME_PATH}/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
    
# Configure Gai
ENV MODEL_PATH="${HOME_PATH}/.gai/models"
ENV CATEGORY="ttt"
RUN echo "{/"app_dir/":/"/${HOME_PATH}/.gai/"}" > ${HOME_PATH}/.gairc
VOLUME ${HOME_PATH}/.gai
