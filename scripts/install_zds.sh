#!/bin/bash

# Install script for the zds-site repository

function _in {
  # credits: https://stackoverflow.com/a/8574392
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

function _nvm {
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
}

function info {
    echo -n -e "\033[0;36m";
    echo "$1";
    echo -n -e "\033[00m";
}

function error {
    echo -n -e "\033[0;31m";
    echo "$1";
    echo -n -e "\033[00m";
}

# variables
source ./scripts/define_variable.sh

# os-specific package install
if  ! $(_in "-packages" $@) && ( $(_in "+packages" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+packages] installing packages (this subcommand will be run as super-user)"
    version=$(cat /proc/version)
    if [[ "$version" =~ "ubuntu" ]]; then
        REALPATH="realpath"
        release=$(lsb_release -c)
        if [[ "$release" =~ "bionic" ]]; then
            REALPATH="coreutils"
        fi
        sudo apt-get -y install git python3-dev python3-venv python3-setuptools libxml2-dev python3-lxml libxslt1-dev zlib1g-dev python3-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip build-essential curl $REALPATH librsvg2-bin imagemagick xzdec
    elif [[ "$version" =~ "debian" ]]; then
        sudo apt-get -y install git python3-dev python3-venv python3-setuptools libxml2-dev python3-lxml libxslt-dev libz-dev python3-sqlparse libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip virtualenv build-essential curl librsvg2-bin imagemagick xzdec
    elif [[ "$version" =~ "fedora" ]]; then
        sudo dnf -y install git python3-devel python3-setuptools libxml2-devel python3-lxml libxslt-devel zlib-devel python3-sqlparse libjpeg-turbo-devel libjpeg-turbo-devel freetype freetype-devel libffi-devel python3-pip python-virtualenv gcc redhat-rpm-config
    elif [[ "$version" =~ "arch" ]]; then
        sudo pacman -Syu git wget python python-setuptools python-pip libxml2 python-lxml libxslt zlib python-sqlparse libffi libjpeg-turbo freetype2 base-devel unzip
    else
        error "!! I did not detect your linux version"
        error "!! Please manually install the packages and run again with \`-packages\`"
        exit 1
    fi
fi

# virtualenv
if  ! $(_in "-virtualenv" $@) && ( $(_in "+virtualenv" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    if [ ! -d $ZDS_VENV ]; then
        info "* [+virtualenv] creating virtualenv"
        python3 -m venv $ZDS_VENV
    fi
fi

if [[ $VIRTUAL_ENV == "" || $(basename $VIRTUAL_ENV) != $ZDS_VENV ]]; then
    info "* activating venv \`$ZDS_VENV\`"

    if [ -d $HOME/.nvm ]; then # force nvm activation, in case of
        _nvm
    fi

    . ./$ZDS_VENV/bin/activate

    if [[ $? != "0" ]]; then
        error "!! no virtualenv, cannot continue"
        exit 1
    fi
fi

# nvm node & yarn
if  ! $(_in "-node" $@) && ( $(_in "+node" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+node] installing nvm (v$ZDS_NVM_VERSION) & node (v$ZDS_NODE_VERSION) & yarn"

    wget -qO- https://raw.githubusercontent.com/creationix/nvm/v${ZDS_NVM_VERSION}/install.sh | bash
    if [[ $? == 0 ]]; then

        _nvm

        # install node & yarn
        nvm install ${ZDS_NODE_VERSION}
        echo ${ZDS_NODE_VERSION} > .nvmrc
        nvm use

        npm -g add yarn

        if [[ $(grep -c -i "nvm use" $VIRTUAL_ENV/bin/activate) == "0" ]]; then # add nvm activation to venv activate's
            ACTIVATE_NVM="nvm use  # activate nvm (from install_zds.sh)"

            echo $ACTIVATE_NVM >> $VIRTUAL_ENV/bin/activate
            echo $ACTIVATE_NVM >> $VIRTUAL_ENV/bin/activate.csh
            echo $ACTIVATE_NVM >> $VIRTUAL_ENV/bin/activate.fish
        fi
    else
        error "!! Cannot obtain nvm v${ZDS_NVM_VERSION}"
        exit 1
    fi
fi

# local elasticsearch
if  ! $(_in "-elastic-local" $@) && ( $(_in "+elastic-local" $@) || $(_in "+full" $@) ); then
    info "* [+elastic-local] installing a local version of elasticsearch (v$ZDS_ELASTIC_VERSION)"
    mkdir -p .local
    cd .local

    if [ -d elasticsearch ]; then # remove previous install
        rm -R elasticsearch
    fi

    wget -q https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ZDS_ELASTIC_VERSION}.zip
    if [[ $? == 0 ]]; then
        unzip elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        rm elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        mv elasticsearch-${ZDS_ELASTIC_VERSION} elasticsearch

        # add options to reduce memory consumption
        info "#Options added by install_zds.sh" >> elasticsearch/config/jvm.options
        info "-Xms512m" >> elasticsearch/config/jvm.options
        info "-Xmx512m" >> elasticsearch/config/jvm.options

        # symbolic link to elastic start script
        ln -s $(realpath elasticsearch/bin/elasticsearch) $VIRTUAL_ENV/bin/
    else
        error "!! Cannot get elasticsearch ${ZDS_ELASTIC_VERSION}"
        exit 1;
    fi;
    cd ..
fi

# local texlive
if  ! $(_in "-tex-local" $@) && ( $(_in "+tex-local" $@) || $(_in "+full" $@) ); then
    info "* [+tex-local] install texlive"

    CURRENT=$(pwd)
    mkdir -p .local
    cd .local
    LOCAL=$CURRENT/.local

    # clone
    BASE_TEXLIVE=$LOCAL/texlive
    BASE_REPO=$BASE_TEXLIVE
    REPO=$BASE_REPO/latex-template

    mkdir -p $BASE_REPO
    cd $BASE_REPO

    if [ -d $REPO ]; then # remove previous version of the template
        rm -Rf $REPO
    fi

    git clone $ZDS_LATEX_REPO
    if [[ $? == 0 ]]; then
        # copy scripts
        cd $BASE_TEXLIVE
        cp $REPO/scripts/texlive.profile $REPO/scripts/packages $REPO/scripts/install_font.sh .

        # install fonts
        ./install_font.sh

        # install texlive
        sed -i 's@.texlive@texlive@' texlive.profile  # change directory
        sed -i "s@\$HOME@$LOCAL@" texlive.profile  # change destination

        wget -q -O install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
        if [[ $? == 0 ]]; then
            if [[ ! -f ./bin/x86_64-linux/tlmgr ]]; then # install texlive
                tar xzf install-tl.tar.gz
                ./install-tl*/install-tl -profile texlive.profile

                # Symlink the binaries to bin of venv
                for i in $BASE_TEXLIVE/bin/x86_64-linux/*; do
                  ln -sf $i $VIRTUAL_ENV/bin/
                done
            fi

            ./bin/x86_64-linux/tlmgr install $(cat packages)  # extra packages
            ./bin/x86_64-linux/tlmgr update --self
            rm -Rf $REPO
        else
            error "!! Cannot download texlive"
            exit 1
        fi
    else
        error "!! cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $CURRENT
fi

# latex-template in TEXMFHOME.
if  ! $(_in "-latex-template" $@) && ( $(_in "+latex-template" $@) || $(_in "+full" $@) ); then
    info "* [+latex-template] install latex-template (from $ZDS_LATEX_REPO)"

    CURRENT=$(pwd)

    if [[ $(which kpsewhich) == "" ]]; then # no texlive ?
        error "!! Cannot find kpsewhich, do you have texlive?"
        exit 1;
    fi

    # clone
    BASE_REPO=$(kpsewhich -var-value TEXMFHOME)/tex/latex
    REPO=$BASE_REPO/latex-template

    if [ -d $REPO ]; then # remove previous version of the template
        rm -Rf $REPO
    fi

    mkdir -p $BASE_REPO
    cd $BASE_REPO

    git clone $ZDS_LATEX_REPO
    if [[ $? != 0 ]]; then
        error "!! cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $CURRENT
fi

# install back
if  ! $(_in "-back" $@) && ( $(_in "+back" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+back] install back dependencies & migration"
    make install-back
    make migrate-db # migration are required for the instance to run properly anyway
fi

# install front
if  ! $(_in "-front" $@) && ( $(_in "+front" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+front] install front dependencies & build front"
    if [ -d node_modules ]; then # delete previous modules
        rm -R node_modules
    fi;

    make install-front
    make build-front
fi

# zmd
if  ! $(_in "-zmd" $@) && ( $(_in "+zmd" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+zmd] install zmarkdown dependencies"
    make zmd-install
fi

# fixtures
if  ! $(_in "-data" $@) && ( $(_in "+data" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    info "* [+data] fixtures"
    make generate-fixtures
fi
info "Done. You can now run instance with \`source $ZDS_VENV/bin/activate\`, and then, \`make zmd-start && make run-back\`"
