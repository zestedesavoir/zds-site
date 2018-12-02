install-linux:
	./scripts/install_zds.sh +base

install-linux-full:
	./scripts/install_zds.sh +full

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

run-elastic:
	elasticsearch || echo 'No elasticsearch installed (you can add it locally with `./scripts/install_zds.sh +elasticsearch`)'

zmd-install:
	cd zmd && npm -g install pm2 && npm install --production

zmd-start:
	cd zmd/node_modules/zmarkdown && npm run server

zmd-stop:
	pm2 kill

zmd-check:
	@curl -s http://localhost:27272 || echo 'Use `make zmd-start` to start zmarkdown server'

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

clean: clean-back clean-front

wipe:
	rm base.db
	rm -rf contents-private/*
	rm -rf contents-public/*

.PHONY: doc
doc:
	cd doc && \
	make html

.PHONY: fixtures
fixtures:
	python manage.py loaddata fixtures/*.yaml
	python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml

restart_db: wipe migrate fixtures
	python manage.py load_fixtures --size=low --all

lint: lint-back lint-front

run:
	make -j2 watch-front run-back

test: test-back test-front

# inspired from https://gist.github.com/sjparkinson/f0413d429b12877ecb087c6fc30c1f0a

.DEFAULT_GOAL := help
help:
	@echo "Use 'make [command]' to run one of these commands:"
	@echo ""
	@fgrep --no-filename "##" ${MAKEFILE_LIST} | head -n '-1' | sed 's/\:.*\#/\: \#/g' | column -s ':#' -t -c 2
	@echo ""
	@echo "Open this Makefile to see what each command does."
