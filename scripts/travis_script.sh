#!/bin/bash

source ./scripts/define_function.sh --travis-output

zds_fold_category "script"

exVal=0


# start elastic
if [[ "$1" == "start_elasticsearch" ]] && [[ "$ZDS_TEST_JOB" == *"zds.searchv2"* ]]; then
    zds_fold_start "elasticsearch" "* Start elasticsearch as service"
        sudo service elasticsearch start; exVal=$?
    zds_fold_end
fi


# start latex
if [[ "$1" == "start_latex" ]] && [[ "$ZDS_TEST_JOB" == *"zds.tutorialv2"* ]]; then
    zds_fold_start "latex" "* Start texhash -> latex"
        texhash; exVal=$?
    zds_fold_end
fi


# lint backend
if [[ "$1" == "lint_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds.gallery"* ]]; then
    zds_fold_start "lint_backend" "* Run lint for backend"
        ./scripts/no_import_zds_settings.sh
        flake8; exVal=$?
        flake8 --config=zds/settings/.flake8 zds/settings; exVal=$? + $exVal
    zds_fold_end
fi

# test backend
if [[ "$1" == "test_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "test_backend" "* Run test for backend"
        python manage.py makemigrations --dry-run --check; exVal=$?
    zds_fold_end
fi


# coverage backend
if [[ "$1" == "coverage_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "coverage_backend" "* Run coverage for backend"
        coverage run --source='.' manage.py \
            test -v=2\
            --keepdb \
            --settings zds.settings.ci_test \
            --exclude-tag=front \
            ${ZDS_TEST_JOB/front/}; exVal=$?
    zds_fold_end
fi


# print zmarkdown log
if [[ "$1" == "print_zmarkdown_log" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "zmarkdown_log" "* Print zmarkdown log"
        pm2 logs --nostream --raw --lines 1000; exVal=$?
    zds_fold_end
fi


# selenium test
if [[ "$1" == "selenium_test" ]]  && [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    zds_fold_start "selenium_test" "* Run selenium test for frontend"
        xvfb-run --server-args="-screen 0 1280x720x8" python manage.py \
            test -v=2\
            --settings zds.settings.ci_test \
            --tag=front \
            --keepdb; exVal=$?
    zds_fold_end
fi


# build documentation
if [[ "$1" == "build_documentation" ]] && [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
    zds_fold_start "doc" "* Run SphinxBuild to build documentation"
        print_info "* Build documentation"
        if [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
            make generate-doc; exVal=$?
        fi
    zds_fold_end
fi


if [[ $exVal != 0 ]]; then
    print_error "!! Some error on the last task ($1)."
    exit 1
fi
