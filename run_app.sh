#!/bin/bash


mongod --dbpath ./db 

source ./venv/bin/activate
python3 app.py

