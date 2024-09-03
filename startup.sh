#!/bin/bash
python -c "import toml; print(toml.load('/workspaces/gai-ttt-svr-llamacpp/pyproject.toml')['project']['version'])"
python main.py