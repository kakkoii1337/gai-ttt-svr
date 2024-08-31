echo "source ~/.venv/bin/activate" >> ~/.bashrc
source ~/.venv/bin/activate
poetry lock --no-update
poetry install