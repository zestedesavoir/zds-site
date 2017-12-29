#!/bin/sh -e

cd "$(dirname "$0")"

cd ..

python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000
