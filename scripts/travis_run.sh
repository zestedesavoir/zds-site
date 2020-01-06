#!/bin/bash


if [[ "$ZDS_TEST_JOB" == "none" ]]; then
    exit 0
fi


function print_info {
    echo -en "\033[0;36m"
    echo "$1"
    echo -en "\033[00m"
}


function error_handler {
    if [[ $exVal != 0 ]]; then
        print_error $1
        exit 1
    fi
}


function run_script {
	./scripts/travis_script.sh $1; exVal=$?
	error_handler "!! Some error on the last task ($1)."
}


function activate_env {
	print_info "source $1/bin/activate"
	source $1/bin/activate; exVal=$?
	error_handler "!! Error: environnement not load.\n - Value = $1"
}


activate_env "./$ZDS_VENV"
	# Add geckodriver in the PATH of zdsenv
        export PATH="$PATH:/home/travis/build/zestedesavoir/zds-site/geckodriver"
        export DISPLAY=":99.0"
	# Use hack for virtualenv (fix some task with "command not found")
	export PATH="$PATH:/home/travis/virtualenv/python${TRAVIS_PYTHON_VERSION}/bin"

	run_script "start_elasticsearch"

	run_script "make_migrations"

	run_script "lint_frontend"

	run_script "print_zmarkdown_log"

	run_script "selenium_test"

	run_script "coverage_backend"

	run_script "lint_backend"

	run_script "build_documentation"

