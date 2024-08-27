#!/bin/bash
source /root/.venv/bin/activate \
&& python -c "import toml; print(toml.load('/app/pyproject.toml')['tool']['poetry']['version'])" \
&& python main.py