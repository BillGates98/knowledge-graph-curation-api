#!/bin/bash

python3 main/manage.py makemigrations
python3 main/manage.py migrate
python3 main/manage.py runserver 0.0.0.0:8000