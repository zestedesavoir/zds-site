#!/bin/sh -e

cd "$(dirname "$0")"

cd ..

python manage.py migrate --settings zds.settings.docker_dev
exec python manage.py runserver 0.0.0.0:8000 --settings zds.settings.docker_dev
