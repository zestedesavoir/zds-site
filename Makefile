## ~ General

install-linux: ## Install the minimal components needed
	./scripts/install_zds.sh +base

install-linux-full: ## Install all the components needed
	./scripts/install_zds.sh +full

update: install-back install-front zmd-install migrate-db build-front ## Update the environment (`install-back` & `install-front` & `zmd-install` & `migrate-db` & `build-front`)

new-db: wipe-db migrate-db generate-fixtures ## Create a new full database (`wipe-db` & `migrate-db` & `generate-fixtures`)

run: ## Run the backend server and watch the frontend (`watch-front` in parallel with `run-back`)
	make -j2 watch-front run-back

run-fast: ## Run the backend in fast mode (no debug toolbar & full cache) and watch the frontend (`watch-front` + `run-back-fast`)
	make -j2 watch-front run-back-fast

lint: lint-back lint-front ## Lint everything (`lint-back` & `lint-front`)

test: test-back test-back-selenium ## Test everything (`test-back` & `test-back-selenium`)

clean: clean-back clean-front ## Clean everything (`clean-back` & `clean-front`)

##
## ~ Backend

install-back: ## Install the Python packages for the backend
	pip install --upgrade -r requirements-dev.txt

install-back-with-prod:
	pip install --upgrade -r requirements-dev.txt -r requirements-prod.txt

run-back: zmd-check ## Run the backend server
	python manage.py runserver --nostatic

run-back-fast: zmd-check ## Run the backend server in fast mode (no debug toolbar & full browser cache)
	python manage.py runserver --settings zds.settings.dev_fast

lint-back: ## Lint Python code
	flake8 zds

test-back: clean-back zmd-start ## Run backend unit tests
	python manage.py test --settings zds.settings.test --exclude-tag=front
	make zmd-stop

test-back-selenium: ## Run backend Selenium tests
	xvfb-run --server-args="-screen 0 1280x720x8" python manage.py test --settings zds.settings.test --tag=front

clean-back: ## Remove Python bytecode files (*.pyc)
	find . -name '*.pyc' -exec rm {} \;

##
## ~ Frontend

install-front: ## Install the Node.js packages for the frontend
	yarn install

build-front: ## Build the frontend assets (CSS, JS, images)
	yarn run build

watch-front: ## Build the frontend assets when they are modified
	yarn run watch --speed

format-front: ## Format the Javascript code
	yarn run lint --fix

lint-front: ## Lint the Javascript code
	yarn run lint

clean-front: ## Clean the frontend builds
	yarn run clean

##
## ~ zmarkdown

ZMD_URL="http://localhost:27272"

zmd-install: ## Install the Node.js packages for zmarkdown
	cd zmd && npm install --production

zmd-start: ## Start the zmarkdown server
	cd zmd/node_modules/zmarkdown && npm run server

zmd-check: ## Check if the zmarkdown server is running
	@curl -s $(ZMD_URL) || echo 'Use `make zmd-start` to start zmarkdown server'

zmd-stop: ## Stop the zmarkdown server
	node ./zmd/node_modules/pm2/bin/pm2 kill

##
## ~ Elastic Search

run-elasticsearch: ## Run the Elastic Search server
	elasticsearch || echo 'No Elastic Search installed (you can add it locally with `./scripts/install_zds.sh +elastic-local`)'

index-all: ## Index the database in a new Elastic Search index
	python manage.py es_manager index_all

index-flagged: ## Index the database in the current Elastic Search index
	python manage.py es_manager index_flagged

##
## ~ PDF

generate-pdf: ## Generate PDFs of published contents
	python manage.py generate_pdf

##
## ~ Database

migrate-db: ## Create or update database schema
	python manage.py migrate

generate-fixtures: ## Generate fixtures (users, tutorials, articles, opinions, topics, licenses...)
	@if curl -s $(ZMD_URL) > /dev/null; then \
		python manage.py loaddata fixtures/*.yaml; \
		python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml; \
		python manage.py load_fixtures --size=low --all; \
	else \
		echo 'Start zmarkdown first with `make zmd-start`'; \
	fi

wipe-db: ## Remove the database and the contents directories
	rm -f base.db
	rm -rf contents-private/*
	rm -rf contents-public/*

##
## ~ Tools

generate-doc: ## Generate the project's documentation
	cd doc && make html
	@echo ""
	@echo "Open 'doc/build/html/index.html' to read the documentation'"

generate-release-summary: ## Generate a release summary from Github's issues and PRs
	@python scripts/generate_release_summary.py

start-publication-watchdog: ## Start the publication watchdog
	@if curl -s $(ZMD_URL) > /dev/null; then \
		python manage.py publication_watchdog; \
	else \
		echo 'Start zmarkdown first with `make zmd-start`'; \
	fi

# inspired from https://gist.github.com/sjparkinson/f0413d429b12877ecb087c6fc30c1f0a

.DEFAULT_GOAL := help
help: ## Show this help
	@echo "Use 'make [command]' to run one of these commands:"
	@echo ""
	@fgrep --no-filename "##" ${MAKEFILE_LIST} | head -n '-1' | sed 's/\:.*\#/\: \#/g' | column -s ':#' -t -c 2
	@echo ""
	@echo "Open this Makefile to see what each command does."
