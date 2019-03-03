#!/bin/bash

function print_info {
    echo -n -e "\033[0;36m";
    echo "$1";
    echo -n -e "\033[00m";
}

# start elastic
if [[ "$1" == "start_elasticsearch" ]] && [[ "$ZDS_TEST_JOB" == *"zds.searchv2"* ]]; then
    print_info "* Start elasticsearch as service"
    sudo service elasticsearch start
fi

# start latex
if [[ "$1" == "start_elasticsearch" ]] && [[ "$ZDS_TEST_JOB" == *"zds.tutorialv2"* ]]; then
    print_info "* Start texhash"
    texhash
fi

# lint backend
if [[ "$1" == "lint_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds.gallery"* ]]; then
    print_info "* Run lint for backend"
    ./scripts/no_import_zds_settings.sh \
    && flake8 \
    && flake8 --config=zds/settings/.flake8 zds/settings
fi

# test backend
if [[ "$1" == "test_backend" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    print_info "* Run test for backend"
    python manage.py makemigrations --dry-run --check \
    && coverage run --source='.' manage.py \
        test -v=2\
        --keepdb \
        --settings zds.settings.ci_test \
        --exclude-tag=front \
        ${1/front/}
fi

# print zmarkdown log
if [[ "$1" == "print_zmarkdown_log" ]] && [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
    print_info "* Print zmarkdown log"
    pm2 logs --nostream --raw --lines 1000
fi

# selenium test
if [[ "$1" == "selenium_test" ]]  && [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    print_info "* Run selenium test for frontend"
    xvfb-run --server-args="-screen 0 1280x720x8" python manage.py \
        test -v=2\
        --settings zds.settings.ci_test \
        --tag=front \
        --keepdb
fi

# build documentation
if [[ "$1" == "build_documentation" ]] && [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
    print_info "* Build documentation"
    if [[ "$ZDS_TEST_JOB" == *"doc"* ]]; then
        generate-doc
    fi
fi
