#!/bin/bash
source /root/.venv/bin/activate \
&& python -c "import toml; print(toml.load('/workspaces/gai-ttt-svr/pyproject.toml')['tool']['poetry']['version'])" \
&& python main.py