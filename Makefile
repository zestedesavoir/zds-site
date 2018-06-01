.PHONY: fixtures

all: help

# install
## linux
install-debian:
	sudo apt-get install git python3-dev python3-setuptools libxml2-dev python3-lxml libxslt-dev libz-dev python3-sqlparse libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip build-essential

install-ubuntu:
	sudo apt-get install git python3-dev python3-setuptools libxml2-dev python3-lxml libxslt1-dev libz-dev python3-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip build-essential

install-fedora:
	sudo dnf install git python3-devel python3-setuptools libxml2-devel python3-lxml libxslt-devel zlib-devel python3-sqlparse libjpeg-turbo-devel libjpeg-turbo-devel freetype freetype-devel libffi-devel python3-pip gcc redhat-rpm-config

install-archlinux:
	sudo pacman -Sy git python python-setuptools python-pip libxml2 python-lxml libxslt zlib python-sqlparse libffi libjpeg-turbo freetype2 base-devel

install-macos:
	brew install gettext cairo --without-x11 py2cairo node && \
	pip3 install virtualenv virtualenvwrapper

# dev back
## django
generate-pdf:
	python manage.py generate_pdf

migrate:
	python manage.py migrate

reset:
	python manage.py reset

shell:
	python manage.py shell

index-all:
	python manage.py es_manager index_all

index-flagged:
	python manage.py es_manager index_flagged

## back-utils
clean-back:
	find . -name '*.pyc' -exec rm {} \;

install-back:
	pip3 install --upgrade -r requirements-dev.txt

lint-back:
	flake8 zds

report-release-back:
	python scripts/release_generator.py

run-back: zmd-check
	python manage.py runserver

test-front:
	python manage.py test --settings zds.settings.test --tag=front

test-back: clean-back zmd-start
	python manage.py test --settings zds.settings.test --exclude-tag=front
	make zmd-stop

# zmd

zmd-install:
	cd zmd && yarn --non-interactive --frozen-lockfile --production

zmd-start:
	cd zmd/node_modules/zmarkdown && npm run server

zmd-stop:
	pm2 kill

zmd-check:
	@curl -s http://localhost:27272 || echo 'Use `make zmd-start` to start zmarkdown server'


# front
## front-utils

build-front:
	yarn run build

clean-front:
	yarn run clean

install-front:
	yarn

lint-front:
	yarn run lint

watch-front:
	yarn run gulp

# generic utils

clean: clean-back clean-front

wipe:
	rm base.db
	rm -rf contents-private/*
	rm -rf contents-public/*

doc:
	cd doc && \
	make html

fixtures:
	python manage.py loaddata fixtures/*.yaml
	python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml

restart_db: wipe migrate fixtures
	python manage.py load_fixtures --size=low --all

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build-front       to build frontend code"
	@echo "  doc               to generate the html documentation"
	@echo "  fixtures          to load every fixtures"
	@echo "  generate-pdf      to regenerate all PDFs"
	@echo "  index-all         to setup and (re)index all things for search"
	@echo "  index-flagged     to index flagged things for search"
	@echo "  help              to get this help"
	@echo "  install-back      to install backend dependencies"
	@echo "  install-front     to install frontend dependencies"
	@echo "  install-debian    to install debian dependencies"
	@echo "  install-ubuntu    to install ubuntu dependencies"
	@echo "  install-fedora    to install fedora dependencies"
	@echo "  install-archlinux to install archlinux dependencies"
	@echo "  install-macos       to install os x dependencies"
	@echo "  lint-back         to lint backend code (flake8)"
	@echo "  lint-front        to lint frontend code (jshint)"
	@echo "  clean-back        to clean *.pyc"
	@echo "  clean-front       to clean frontend builds"
	@echo "  clean             to clean everything"
	@echo "  wipe              to clean data (database and contents)"
	@echo "  watch-front       to watch frontend code"
	@echo "  migrate           to migrate the project"
	@echo "  report-release-back  to generate release report"
	@echo "  run               to run the project locally"
	@echo "  run-back          to only run the backend"
	@echo "  shell             to get django shell"
	@echo "  test              to run django tests"
	@echo "Open this Makefile to see what each target does."
	@echo "When a target uses an env variable (eg. $$(VAR)), you can do"
	@echo "  make VAR=my_var cible"

install: install-back install-front

lint: lint-back lint-front

run:
	make -j2 watch-front run-back

test: test-back test-front
