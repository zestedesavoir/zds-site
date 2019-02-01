#!/bin/bash

zds_install_argument=""
function zds_register_for_install {
    if [[ "$zds_install_argument" == "" ]]; then
        zds_install_argument="$1"
    else
        zds_install_argument="$zds_install_argument $1"
    fi
}

function print_info {
    echo -n -e "\033[0;36m";
    echo "$1";
    echo -n -e "\033[00m";
}

function install_geckodriver {
    print_info "* Install webdriver for selenium."

    if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
        wget "https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz" \
            && mkdir "geckodriver" \
            && tar -xzf "geckodriver-v0.23.0-linux64.tar.gz" -C "geckodriver" \
            && export PATH="$PATH:$PWD/geckodriver" \
            && export DISPLAY=":99.0"
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
