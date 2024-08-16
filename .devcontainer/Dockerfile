FROM kakkoii1337/torch2.2.0-cuda12.1-ubuntu22.04-base:latest as build

# Step 1: Install poetry
ENV PATH="/root/.local/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive PIP_PREFER_BINARY=1
RUN poetry config virtualenvs.create false

# Step 2: Install VSCode Extensions and dev tools
RUN pip install notebook jupyterlab ipywidgets ipykernel pytest

## Step 3: Install exllamav2
RUN pip install https://github.com/turboderp/exllamav2/releases/download/v0.1.8/exllamav2-0.1.8+cu121.torch2.2.2-cp310-cp310-linux_x86_64.whl
    
# Step 4: Configure Gai
ENV MODEL_PATH="/root/.gai/models"
ENV CATEGORY="itt"
RUN echo '{"app_dir":"/root/.gai"}' > /root/.gairc
VOLUME /root/.gai


