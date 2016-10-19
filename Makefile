all: help

# install
## linux
install-debian:
	sudo apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev libffi-dev python-pip python-tox build-essential

install-ubuntu:
	sudo apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt1-dev libz-dev python-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev libffi-dev python-pip python-tox build-essential

install-fedora:
	sudo dnf install git python-devel python-setuptools libxml2-devel python-lxml libxslt-devel zlib-devel python-sqlparse libjpeg-turbo-devel libjpeg-turbo-devel freetype freetype-devel libffi-devel python-pip python-tox gcc redhat-rpm-config

install-osx:
	brew install virtualenv_select py27-virtualenv py27-virtualenvwrapper py27-tox node

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

## back-utils
clean-back:
	find . -name '*.pyc' -exec rm {} \;

install-back:
	pip install --upgrade -r requirements.txt -r requirements-dev.txt

lint-back:
	flake8 --exclude=migrations --max-line-length=120 zds

report-release-back:
	python scripts/release_generator.py

run-back:
	python manage.py runserver 0.0.0.0:8000

test-back:
	make clean-back && \
	python manage.py test --settings zds.settings_test_local

# front
## front-utils

build-front:
	npm run build

clean-front:
	npm run clean

install-front:
	npm install

lint-front:
	npm run lint

watch-front:
	npm run gulp

# generic utils

clean: clean-back clean-front

doc:
	cd doc && \
	make html

.PHONY: fixtures
fixtures:
	python manage.py loaddata fixtures/*.yaml

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build-front       to build frontend code"
	@echo "  doc               to generate the html documentation"
	@echo "  fixtures          to load every fixtures"
	@echo "  generate-pdf      to regenerate all PDFs"
	@echo "  help              to get this help"
	@echo "  install-back      to install backend dependencies"
	@echo "  install-front     to install frontend dependencies"
	@echo "  install-debian    to install debian dependencies"
	@echo "  install-ubuntu    to install ubuntu dependencies"
	@echo "  install-fedora    to install fedora dependencies"
	@echo "  install-osx       to install os x dependencies"
	@echo "  lint-back         to lint backend code (flake8)"
	@echo "  lint-front        to lint frontend code (jshint)"
	@echo "  clean-back        to clean *.pyc"
	@echo "  clean-front       to clean frontend builds"
	@echo "  clean             to clean everything"
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

test: test-back

travis:
	tox $TEST_APP # set by travis, see .travis.yml
