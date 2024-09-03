#!/bin/bash
python -c "import toml; print(toml.load('/workspaces/gai-ttt-svr-exllamav2/pyproject.toml')['project']['version'])"
python main.py