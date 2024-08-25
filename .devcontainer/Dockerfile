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

USER kakkoii1337

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
ENV PATH="/root/.local/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false \
    && apt remove -y curl

# Step 2: Install exllamav2
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ ! -f /root/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl ]; then \
        wget https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl -P /root/.cache/pip; \
    fi \
    && pip install /root/.cache/pip/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
    
# Configure Gai
ENV MODEL_PATH="/root/.gai/models"
ENV CATEGORY="ttt"
RUN echo '{"app_dir":"/root/.gai"}' > /root/.gairc
VOLUME /root/.gai


