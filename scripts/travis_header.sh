#!/bin/bash

zds_install_argument=""
function zds_register_for_install {
    if [[ "$zds_install_argument" == "" ]]; then
        zds_install_argument="$1"
    else
        zds_install_argument="$zds_install_argument $1"
    fi
}

function zds_register_module_for_installation {
    zds_register_for_install "+base +prod"

    # install elastic-local
    if [[ "$ZDS_TEST_JOB" == *"zds.searchv2"* ]]; then
        print_info "* Register elasticsearch with jdk. It needed to test : zds.searchv2."
        zds_register_for_install "+jdk-local +elastic-local"
    fi

    # install latex
    if [[ "$ZDS_TEST_JOB" == *"zds.tutorialv2"* ]]; then
        print_info "* Register latex for zds.tutorialv2."
        zds_register_for_install "+tex-local +latex-template"
    fi

    # install backend dependencies
    if ! ( [[ "$ZDS_TEST_JOB" == *"zds."* ]] || [[ "$ZDS_TEST_JOB" == *"selenium"* ]] || [[ "$ZDS_TEST_JOB" == *"doc"* ]] ); then
        print_info "* Don't register back because zds.* task, selenium and doc are not installed."
        zds_register_for_install "-back"
    fi

    print_info "* Argument for installation : $zds_install_argument"
}

function install_geckodriver {
    if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
        wget "https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz" \
            && mkdir "geckodriver" \
            && tar -xzf "geckodriver-v0.23.0-linux64.tar.gz" -C "geckodriver" \
            && export PATH="$PATH:$PWD/geckodriver" \
            && export DISPLAY=":99.0"
    fi
}

source ./scripts/define_variable.sh
source ./scripts/define_function.sh --travis-output

zds_fold_category "before_install"

zds_fold_start "packages" "* update apt-get (for newest dependencies version)"
    sudo apt-get update -qq
zds_fold_end

zds_fold_start "coveralls" "* update apt-get"
    pip install -q coveralls
zds_fold_end

zds_fold_start "ci_turbo" "* Skip task depending on directory changes (task will run only if needed)"
    source ./scripts/ci_turbo.sh # This script exports environment variables, it must be sourced
zds_fold_end

if [[ "$ZDS_TEST_JOB" == *"zds."* ]] || [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    #display print_info
    forwho=""
    if [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
        forwho="'zds.*' tasks (-> needed for tests)"

        if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
            forwho="$forwho and selenium"
        fi
    else
        forwho="selenium"
    fi

    zds_fold_start "mysql" "* Install mysql for $forwho."
        ./scripts/ci_mysql_setup.sh
    zds_fold_end
fi

if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    zds_fold_start "webdriver" "* Install webdriver for selenium"
        install_geckodriver
    zds_fold_end
fi

zds_fold_start "register_module" "* Register module for installation"
    zds_register_module_for_installation
zds_fold_end
