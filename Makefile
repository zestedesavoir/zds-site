## ~ General

install-linux: ## Install the minimal components needed
	./scripts/install_zds.sh +base

install-linux-full: ## Install all the components needed
	./scripts/install_zds.sh +full

new-db: wipe-db migrate-db generate-fixtures ## Create a new full database (`wipe-db` & `migrate-db` & `generate-fixtures`)

run: ## Run the backend server and watch the frontend (`watch-front` in parallel with `run-back`)
	make -j2 watch-front run-back

lint: lint-back lint-front ## Lint everything (`lint-back` & `lint-front`)

test: test-back test-back-selenium ## Test everything (`test-back` & `test-back-selenium`)

clean: clean-back clean-front ## Clean everything (`clean-back` & `clean-front`)

##
## ~ Backend

install-back: activate-venv ## Install the Python packages for the backend
	pip install --upgrade -r requirements-dev.txt

install-back-with-prod: activate-venv
	pip install --upgrade -r requirements-dev.txt -r requirements-prod.txt

run-back: activate-venv zmd-start ## Run the backend server
	python manage.py runserver
	make zmd-stop

lint-back: activate-venv ## Lint Python code
	flake8 zds

test-back: activate-venv clean-back zmd-start ## Run backend unit tests
	python manage.py test --settings zds.settings.test --exclude-tag=front
	make zmd-stop

test-back-selenium: activate-venv ## Run backend Selenium tests
	xvfb-run --server-args="-screen 0 1280x720x8" python manage.py test --settings zds.settings.test --tag=front

clean-back: ## Remove Python bytecode files (*.pyc)
	find . -name '*.pyc' -exec rm {} \;

##
## ~ Frontend

install-front: activate-venv ## Install the Node.js packages for the frontend
	yarn install

build-front: activate-venv ## Build the frontend assets (CSS, JS, images)
	yarn run build

watch-front: activate-venv ## Build the frontend assets when they are modified
	yarn run watch --speed

lint-front: activate-venv ## Lint the frontend's Javascript
	yarn run lint

clean-front: activate-venv ## Clean the frontend builds
	yarn run clean

##
## ~ zmarkdown

zmd-install: activate-venv ## Install the Node.js packages for zmarkdown
	cd zmd && npm -g install pm2 && npm install --production

zmd-start: activate-venv ## Start the zmarkdown server if needed
    @curl -s http://localhost:27272 || (cd zmd/node_modules/zmarkdown && npm run server)

zmd-stop: activate-venv ## Stop the zmarkdown server
	pm2 kill

##
## ~ Elastic Search

run-elasticsearch: activate-venv ## Run the Elastic Search server
	elasticsearch || echo 'No Elastic Search installed (you can add it locally with `./scripts/install_zds.sh +elastic-local`)'

index-all: activate-venv ## Index the database in a new Elastic Search index
	python manage.py es_manager index_all

index-flagged: activate-venv ## Index the database in the current Elastic Search index
	python manage.py es_manager index_flagged

##
## ~ PDF

generate-pdf: activate-venv ## Generate PDFs of published contents
	python manage.py generate_pdf

##
## ~ Database

migrate-db: activate-venv ## Create or update database schema
	python manage.py migrate

generate-fixtures: activate-venv zmd-start ## Generate fixtures (users, tutorials, articles, opinions, topics...)
	python manage.py loaddata fixtures/*.yaml
	python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml
	python manage.py load_fixtures --size=low --all
	make zmd-stop

wipe-db: ## Remove the database and the contents directories
	rm -f base.db
	rm -rf contents-private/*
	rm -rf contents-public/*

##
## ~ Tools

activate-venv:
    source zdsenv/bin/activate

generate-doc: activate-venv ## Generate the project's documentation
	cd doc && make html
	@echo ""
	@echo "Open 'doc/build/html/index.html' to read the documentation'"

generate-release-summary: ## Generate a release summary from Github's issues and PRs
	@python scripts/generate_release_summary.py

start-publication-watchdog: activate-venv zmd-start ## Start the publication watchdog
	python manage.py publication_watchdog
	make zmd-stop

# inspired from https://gist.github.com/sjparkinson/f0413d429b12877ecb087c6fc30c1f0a

.DEFAULT_GOAL := help
help: ## Show this help
	@echo "Use 'make [command]' to run one of these commands:"
	@echo ""
	@fgrep --no-filename "##" ${MAKEFILE_LIST} | head -n '-1' | sed 's/\:.*\#/\: \#/g' | column -s ':#' -t -c 2
	@echo ""
	@echo "Open this Makefile to see what each command does."
