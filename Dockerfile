# syntax=docker/dockerfile:1.2
FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda

#Step 1: Install deps and poetry
RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends \
        curl \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Step 2: Install poetry
ARG HOME_PATH="/root"
RUN curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Create and activate virtual environment
RUN python -m venv ${HOME_PATH}/.venv \
    # disable virtual env management by poetry
    && poetry config virtualenvs.create false

# Run bash shell so that we can use source
SHELL ["/bin/bash","-c"]

# Install dependencies
ENV CACHE_PATH=${HOME_PATH}/.cache/pypoetry
RUN --mount=type=cache,target=${CACHE_PATH} \
    source ${HOME_PATH}/.venv/bin/activate \
    && pip install "torch==2.2.0" \
    && pip install "numpy==1.26.4" \
    && if [ ! -f "${HOME}/.cache/pypoetry/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" ]; then \
         wget "https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" -P ${HOME}/.cache/pypoetry; \
        fi \
        && pip install "${HOME}/.cache/pypoetry/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl"

# Step 3: Copy Source Code
WORKDIR /app
COPY src/gai/ttt/server src/gai/ttt/server
COPY pyproject.toml poetry.lock ./

# Step 4: Install project
RUN --mount=type=cache,target=${CACHE_PATH} \
    source ${HOME_PATH}/.venv/bin/activate \
    && poetry install --no-interaction --no-ansi -vv 

# Step 5: Startup
RUN echo '{"app_dir":"/app/.gai"}' > ${HOME_PATH}/.gairc \
    && echo "source ~/.venv/bin/activate" >> ~/.bashrc
VOLUME /app/.gai
ENV MODEL_PATH="/app/.gai/models"
ENV CATEGORY=${CATEGORY}
WORKDIR /app/src/gai/ttt/server/api
COPY startup.sh .
CMD ["bash","startup.sh"]