#!/bin/bash

# Navigasi ke direktori proyek
cd "$(dirname "$0")"

# Menjalankan MongoDB di terminal terpisah
gnome-terminal -- bash -c "mongod --dbpath ./db --logpath ./db/mongod.log --fork; exec bash"

# Mengaktifkan virtual environment dan menjalankan Flask app dalam terminal ini
source ./venv/bin/activate
python3 app.py

