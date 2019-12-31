#!/bin/bash

source ./scripts/define_function.sh --travis-output

zds_fold_category "script"

exVal=0


# start elastic
if [[ "$1" == "start_elasticsearch" ]] && [[ "$ZDS_TEST_JOB" == *"zds.searchv2"* ]]; then
    zds_fold_start "elasticsearch" "* Start elasticsearch as service"
        sudo service elasticsearch start; exVal=$?

        gateway "!! elasticsearch didn't start" $exVal
    zds_fold_end
fi


# start latex
if [[ "$1" == "start_latex" ]] && [[ "$ZDS_TEST_JOB" == *"zds.tutorialv2"* ]]; then
    zds_fold_start "latex" "* Start texhash -> latex"
        texhash; exVal=$?

        gateway "!! Texhash failed" $exVal
    zds_fold_end
fi


# lint backend
if [[ "$1" == "lint_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds.gallery"* ]]; then
    zds_fold_start "lint_backend" "* Run lint for backend"
        ./scripts/no_import_zds_settings.sh \
            && flake8 \
            && flake8 --config=zds/settings/.flake8 zds/settings; exVal=$?

        gateway "!! Test failed" $exVal
    zds_fold_end
fi

# test backend
if [[ "$1" == "test_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "test_backend" "* Run test for backend"
        python manage.py makemigrations --dry-run --check; exVal=$?

        gateway "!! Test failed" $exVal
    zds_fold_end
fi


# lint frontend
if [[ "$1" == "lint_frontend" ]] && [[ "$ZDS_TEST_JOB" == *"front"* ]]; then
    zds_fold_start "lint_frontend" "* Run lint for frontend"
        npm run lint; exVal=$?

        gateway "!! Test failed" $exVal
    zds_fold_end
fi


# coverage backend
if [[ "$1" == "coverage_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "coverage_backend" "* Run coverage for backend"

        zds_start_zmd

        coverage run --source='.' manage.py \
            test -v=2\
            --keepdb \
            --settings zds.settings.ci_test \
            --exclude-tag=front \
            ${ZDS_TEST_JOB/front/}; exVal=$?

        gateway "!! Test failed" $exVal

        zds_stop_zmd

    zds_fold_end
fi


# print zmarkdown log
if [[ "$1" == "print_zmarkdown_log" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    zds_fold_start "zmarkdown_log" "* Print zmarkdown log"
        pm2 logs --nostream --raw --lines 1000
    zds_fold_end
fi


# selenium test
if [[ "$1" == "selenium_test" ]]  && [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    zds_fold_start "selenium_test" "* Run selenium test for frontend"

        zds_start_zmd

        xvfb-run --server-args="-screen 0 1280x720x8" python manage.py \
            test -v=2\
            --settings zds.settings.ci_test \
            --tag=front \
            --keepdb; exVal=$?
            
        gateway "!! Test failed" $exVal

        zds_stop_zmd

    zds_fold_end
fi


# build documentation
if [[ "$1" == "build_documentation" ]] && [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
    zds_fold_start "doc" "* Run SphinxBuild to build documentation"
        print_info "* Build documentation"
        if [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
            make generate-doc; exVal=$?
            gateway "!! Build documentation failed" $exVal
        fi
    zds_fold_end
fi
