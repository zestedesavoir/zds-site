#!/bin/bash

zds_fold_category "script"

print_info "source ./\$ZDS_VENV/bin/activate"

source ./$ZDS_VENV/bin/activate

./scripts/travis_script.sh "start_elasticsearch"

./scripts/travis_script.sh "start_latex"

./scripts/travis_script.sh "lint_backend"

./scripts/travis_script.sh "test_backend"

./scripts/travis_script.sh "print_zmarkdown_log"

./scripts/travis_script.sh "selenium_test"

print_info "source ./\$HACK_VIRTUALENV/bin/activate"

source $HACK_VIRTUALENV/bin/activate # Fix task with "command not found"

./scripts/travis_script.sh "coverage_backend"

./scripts/travis_script.sh "build_documentation"
