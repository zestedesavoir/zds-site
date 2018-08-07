.PHONY: fixtures

all: help

# install
## linux
install-linux:
	./scripts/install_zds.sh +base

install-linux-full:
	./scripts/install_zds.sh +full

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
	./scripts/install_zds.sh +back

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

# elasticsearch
run-elastic:
	elasticsearch || echo 'No elasticsearch installed (you can add it locally with `./scripts/install_zds.sh +elasticsearch`)'

# zmd

zmd-install:
	./scripts/install_zds.sh +zmd

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
	./scripts/install_zds.sh +front

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
	./scripts/install_zds.sh +data

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
	@echo "  run-elastic       to run elasticsearch"
	@echo "  shell             to get django shell"
	@echo "  test              to run django tests"
	@echo "Open this Makefile to see what each target does."
	@echo "When a target uses an env variable (eg. $$(VAR)), you can do"
	@echo "  make VAR=my_var cible"

lint: lint-back lint-front

run:
	make -j2 watch-front run-back

test: test-back test-front
