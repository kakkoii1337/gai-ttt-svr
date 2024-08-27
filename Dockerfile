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

# Install poetry
ARG HOME_PATH="/root"
RUN curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Create and activate virtual environment
RUN python -m venv ${HOME_PATH}/venv \
    # disable virtual env management by poetry
    && poetry config virtualenvs.create false

# enable source
SHELL ["/bin/bash","-c"]
ENV PATH="${HOME_PATH}/venv/bin/python:${PATH}"

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

# Step 3: Copy Source Code
WORKDIR /app
COPY src/gai/ttt/server src/gai/ttt/server
COPY pyproject.toml poetry.lock ./

# RUN poetry export --output=requirements.txt

# # Step 4: Install gai-ttt-svr
# RUN --mount=type=cache,target=${CACHE_PATH} \
#     pip install  --disable-pip-version-check --no-deps --requirement=/app/requirements.txt --only-binary :all:

# Step 5: Install project
RUN --mount=type=cache,target=${CACHE_PATH} \
    source ${HOME_PATH}/venv/bin/activate \
    poetry install --no-interaction --no-ansi -vv

# # Step 6: Startup
# RUN echo '{"app_dir":"/app/.gai"}' > ${HOME_PATH}/.gairc
# VOLUME /app/.gai
# ENV MODEL_PATH="/app/.gai/models"
# ENV CATEGORY=${CATEGORY}
# WORKDIR /app/src/gai/ttt/server/api

# # Step 7: Create get_version.sh script
# # RUN source ${HOME_PATH}/venv/bin/activate && \
# #     echo '#!/bin/bash' > /app/src/gai/ttt/server/api/get_version.sh && \
# #     echo "python -c \"import toml; print(toml.load('/app/pyproject.toml')['tool']['poetry']['version'])\"" >> /app/src/gai/ttt/server/api/get_version.sh && \
# #     chmod +x /app/src/gai/ttt/server/api/get_version.sh
# # CMD ["bash", "-c", "./get_version.sh; echo 'Starting main.py...'; source /root/venv/bin/activate && python main.py"]

# COPY startup.sh /app/src/gai/ttt/server/api/
# CMD ["bash","startup.sh"]