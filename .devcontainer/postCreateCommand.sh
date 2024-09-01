# echo "source ~/.venv/bin/activate" >> ~/.bashrc
# source ~/.venv/bin/activate
poetry lock --no-update
poetry install
ls ~/.venv/lib/python3.10/site-packages