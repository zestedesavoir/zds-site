install-linux:
	./scripts/install_zds.sh +base

install-linux-full:
	./scripts/install_zds.sh +full

generate-pdf:
	python manage.py generate_pdf

migrate-db: ## Create or update database schema
	python manage.py migrate

index-all: ## Index the database in a new Elastic Search index
	python manage.py es_manager index_all

index-flagged: ## Index the database in the current Elastic Search index
	python manage.py es_manager index_flagged

clean-back:
	find . -name '*.pyc' -exec rm {} \;

install-back:
	pip3 install --upgrade -r requirements-dev.txt

lint-back:
	flake8 zds

generate-release-summary: ## Generate a release summary from Github's issues and PRs
	@python scripts/generate_release_summary.py

run-back: zmd-check
	python manage.py runserver

test-front:
	python manage.py test --settings zds.settings.test --tag=front

test-back: clean-back zmd-start
	python manage.py test --settings zds.settings.test --exclude-tag=front
	make zmd-stop

run-elasticsearch: ## Run the Elastic Search server
	elasticsearch || echo 'No Elastic Search installed (you can add it locally with `./scripts/install_zds.sh +elasticsearch`)'

zmd-install:
	cd zmd && npm -g install pm2 && npm install --production

zmd-start:
	cd zmd/node_modules/zmarkdown && npm run server

zmd-stop:
	pm2 kill

zmd-check:
	@curl -s http://localhost:27272 || echo 'Use `make zmd-start` to start zmarkdown server'

build-front: ## Build the frontend assets (CSS, JS, images)
	yarn run build

clean-front: ## Clean the frontend builds
	yarn run clean

install-front: ## Install the Node.js packages for the frontend
	yarn install

lint-front: ## Lint the frontend's Javascript
	yarn run lint

watch-front: ## Build the frontend assets when they are modified
	yarn run watch --speed

clean: clean-back clean-front

wipe-db: ## Remove the database and the contents directories
	rm base.db
	rm -rf contents-private/*
	rm -rf contents-public/*

generate-doc: ## Generate the project's documentation
	cd doc && make html
	@echo ""
	@echo "Open 'doc/build/html/index.html' to read the documentation'"

generate-fixtures: ## Generate fixtures (users, tutorials, articles, opinions, topics...)
	python manage.py loaddata fixtures/*.yaml
	python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml
	python manage.py load_fixtures --size=low --all

new-db: wipe-db migrate-db generate-fixtures ## Create a new full database (`wipe-db` & `migrate-db` & `generate-fixtures`)

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
