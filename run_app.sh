#!/bin/bash

# Navigasi ke direktori proyek
cd "$(dirname "$0")"

# Mengaktifkan virtual environment
source ./venv/bin/activate

# Menjalankan MongoDB
mongod --dbpath ./db --logpath ./db/mongod.log --fork

# Menjalankan Flask app
python3 app.py
