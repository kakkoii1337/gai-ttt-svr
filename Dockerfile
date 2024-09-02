FROM debian:stable-slim AS downloader

# Install wget
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN wget "https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" -P "/tmp"

# -----

FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel

ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
ENV TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6+PTX"
ARG CATEGORY=ttt
ARG DEVICE=cuda


# Install exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
# RUN wget "https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl" -P "/tmp"
COPY --from=downloader /tmp/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl /tmp/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
RUN source ${HOME_PATH}/.venv/bin/activate \
    && pip install "/tmp/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl"

# Step 3: Install project
WORKDIR /app
COPY src/gai/ttt/server src/gai/ttt/server
COPY pyproject.toml ./
RUN pip install -e .

# Step 4: Startup
RUN echo '{"app_dir":"/app/.gai"}' > ${HOME_PATH}/.gairc \
    && echo "source ~/.venv/bin/activate" >> ~/.bashrc
VOLUME /app/.gai
ENV MODEL_PATH="/app/.gai/models"
ENV CATEGORY=${CATEGORY}
WORKDIR /app/src/gai/ttt/server/api
COPY startup.sh .
CMD ["bash","startup.sh"]