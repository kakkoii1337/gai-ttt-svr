FROM debian:stable-slim AS downloader

# Install wget
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
ENV LOADER_FILE="exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl"
RUN wget "https://github.com/turboderp/exllamav2/releases/download/v0.1.8/${LOADER_FILE}" -P "/tmp"

# -----

FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

ENV HOME_PATH="/root"
ENV LOADER_FILE="exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl"
ENV PROJECT_NAME="gai-ttt-svr-exllamav2"
ARG CATEGORY=ttt
ARG DEVICE=cuda

# Install exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
COPY --from=downloader "/tmp/${LOADER_FILE}" "/tmp/${LOADER_FILE}"
RUN pip install "/tmp/${LOADER_FILE}"

# Step 3: Install project
WORKDIR /workspaces/${PROJECT_NAME}
COPY src/gai/ttt/server /workspaces/${PROJECT_NAME}/src/gai/ttt/server
COPY pyproject.toml ./
RUN pip install -e .

# Step 4: Startup
RUN echo '{"app_dir":"/root/.gai"}' > ${HOME_PATH}/.gairc
VOLUME /root/.gai
ENV MODEL_PATH="/root/.gai/models"
ENV CATEGORY=${CATEGORY}
WORKDIR /workspaces/${PROJECT_NAME}/src/gai/ttt/server/api
RUN echo 0
COPY startup.sh .
CMD ["bash","startup.sh"]