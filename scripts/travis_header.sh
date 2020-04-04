#!/bin/bash

zds_install_argument=""
function zds_register_for_install() {
    if [[ "$zds_install_argument" == "" ]]; then
        zds_install_argument="$1"
    else
        zds_install_argument="$zds_install_argument $1"
    fi
}

function zds_register_module_for_installation() {
    zds_register_for_install "+base +prod"

    # install elastic-local
    if [[ "$ZDS_TEST_JOB" == *"zds.searchv2"* ]]; then
        print_info "* Register elasticsearch with jdk. It needed to test : zds.searchv2."
        zds_register_for_install "+jdk-local +elastic-local"
    fi

    # install backend dependencies
    if ! ([[ "$ZDS_TEST_JOB" == *"zds."* ]] ||
        [[ "$ZDS_TEST_JOB" == *"selenium"* ]] ||
        [[ "$ZDS_TEST_JOB" == *"doc"* ]]); then
        print_info "* Don't register back because zds.* tasks, doc and selenium are not registered."
        zds_register_for_install "-back"
    else
        print_info "* Back is registered because zds.* tasks, doc or selenium are registered."

        if ! ([[ "$ZDS_TEST_JOB" == *"zds."* ]] ||
            [[ "$ZDS_TEST_JOB" == *"selenium"* ]]); then
            print_info "* Don't migrate-db, if only doc are registered."
            zds_register_for_install "-back-migrate-db"
        fi
    fi

    # install frontend dependencies
    if ! ([[ "$ZDS_TEST_JOB" == *"front"* ]] ||
        [[ "$ZDS_TEST_JOB" == *"selenium"* ]]); then
        print_info "* Don't register front because front task and selenium are not registered."
        zds_register_for_install "-front"
    else
        print_info "* Front is registered because front task or selenium are registered."
    fi

    # Run fixture only when it is asked
    if [[ "$ZDS_TEST_JOB" != *"fixture"* ]]; then
        print_info "* Don't register fixture."
        zds_register_for_install "-data"
    else
        print_info "* Fixture is registered."
    fi

    print_info "* Argument for installation : $zds_install_argument"
}

function install_geckodriver() {
    wget "https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz"
    mkdir "geckodriver"
    tar -xzf "geckodriver-v0.23.0-linux64.tar.gz" -C "geckodriver"
}

source ./scripts/define_variable.sh
source ./scripts/define_function.sh --travis-output

zds_fold_category "before_install"

zds_fold_start "packages" "* [packages] apt-get update : make sure our source list is up-to-date (for newest dependencies version)"
sudo apt-get update -qq
zds_fold_end

zds_fold_start "coveralls" "* [coveralls] Install with pip"
pip install -q coveralls
zds_fold_end

zds_fold_start "ci_turbo" "* [ci_turbo] Skip task depending on directory changes (task will run only if needed)"
source ./scripts/ci_turbo.sh # This script exports environment variables, it must be sourced
zds_fold_end

if [[ "$ZDS_TEST_JOB" == *"zds."* ]] || [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    # display print_info
    forwho=""
    if [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
        forwho="'zds.*' tasks (-> needed for tests)"

        if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
            forwho="$forwho and selenium"
        fi
    else
        forwho="selenium"
    fi

    zds_fold_start "mysql" "* [mysql] Install mysql for $forwho."
    ./scripts/ci_mysql_setup.sh
    zds_fold_end
fi

if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    zds_fold_start "webdriver" "* [webdriver] Install webdriver for selenium"
    install_geckodriver
    zds_fold_end
fi

if [[ "$ZDS_TEST_JOB" == *"zds.tutorialv2"* ]]; then
    # install latex
    zds_fold_start "latex" "* [latex] Install latex & Run texhash (install: texlive + latex-template)"
    # this script is faster than zds_install.sh +tex-local +latex-template
    git clone "$ZDS_LATEX_REPO"
    TEMPLATEDIR=$HOME/.texlive/texmf-local/tex/latex/
    ./latex-template/scripts/install_font.sh
    ./latex-template/scripts/install_texlive.sh
    export PATH=$HOME/.texlive/bin/x86_64-linux:$PATH
    rm -rf "$TEMPLATEDIR/latex-template"
    mkdir -p "$TEMPLATEDIR"
    cp -r ./latex-template "$TEMPLATEDIR"
    texhash
    zds_fold_end
fi

if [[ "$ZDS_TEST_JOB" != "none" ]]; then
    zds_fold_start "register_module" "* [packages] Register module for installation"
    zds_register_module_for_installation
    zds_fold_end
fi
