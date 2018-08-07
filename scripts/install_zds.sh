#!/bin/bash

# Install script for the zds-site repository

function _in {
  # credits: https://stackoverflow.com/a/8574392
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

# variables
if [[ $ZDS_VENV == "" ]]; then
    ZDS_VENV="zdsenv"
fi

if [[ $ZDS_NODE_VERSION == "" ]]; then
    ZDS_NODE_VERSION="10.8.0"
fi

if [[ $ZDS_NVM_VERSION == "" ]]; then
    ZDS_NVM_VERSION="0.33.11"
fi


if [[ $ZDS_ELASTIC_VERSION == "" ]]; then
    ZDS_ELASTIC_VERSION="5.5.2"
fi

if [[ $ZDS_LATEX_REPO == "" ]]; then
    ZDS_LATEX_REPO="https://github.com/zestedesavoir/latex-template.git"
fi


# os-specific package install
if  ! $(_in "-packages" $@) && ( $(_in "+packages" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* installing packages (require sudo)"
    version=$(cat /proc/version)
    if [[ "$version" =~ "ubuntu" ]]; then
        sudo apt-get install git python3-dev python3-setuptools libxml2-dev python3-lxml libxslt1-dev libz-dev python3-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip build-essential curl
    elif [[ "$version" =~ "debian" ]]; then
        sudo apt-get install git python3-dev python3-setuptools libxml2-dev python3-lxml libxslt-dev libz-dev python3-sqlparse libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev libffi-dev python3-pip virtualenv build-essential curl
    elif [[ "$version" =~ "fedora" ]]; then
        sudo dnf install git python3-devel python3-setuptools libxml2-devel python3-lxml libxslt-devel zlib-devel python3-sqlparse libjpeg-turbo-devel libjpeg-turbo-devel freetype freetype-devel libffi-devel python3-pip gcc redhat-rpm-config
    elif [[ "$version" =~ "archlinux" ]]; then
        sudo pacman -Sy git python python-setuptools python-pip libxml2 python-lxml libxslt zlib python-sqlparse libffi libjpeg-turbo freetype2 base-devel
    else
        echo "!! I did not detect your linux version"
        echo '!! Please manually install the packages and run again with `-packages`'
        exit 1
    fi
fi

# virtualenv
if  ! $(_in "-virtualenv" $@) && ( $(_in "+virtualenv" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    if [ ! -d $ZDS_VENV ]; then
        echo "* creating virtualenv"
        virtualenv $ZDS_VENV --python=python3
    fi
fi

if [[ $VIRTUAL_ENV == "" ]]; then
    echo "* activating venv"
    . ./$ZDS_VENV/bin/activate &> /dev/null

    if [[ $? != "0" ]]; then
        echo "!! no virtualenv, cannot continue"
        exit 1
    fi
fi

# nvm node & yarn
if  ! $(_in "-node" $@) && ( $(_in "+node" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* installing nvm (v$ZDS_NVM_VERSION) & node (v$ZDS_NODE_VERSION) & yarn"

    wget -qO- https://raw.githubusercontent.com/creationix/nvm/v${ZDS_NVM_VERSION}/install.sh | bash
    if [[ $? == 0 ]]; then

        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

        # install node & yarn
        nvm install ${ZDS_NODE_VERSION}
        echo ${ZDS_NODE_VERSION} > .nvmrc
        nvm use

        npm -g add yarn

        # add nvm to venv activate scripts:
        ACTIVATE_NVM="nvm use  # activate nvm (from install_zds.sh)"
        echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate
        echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate.csh
        echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate.fish
    else
        echo "!! Cannot obtain nvm"
        exit 1
    fi
fi

# local node & yarn
if  ! $(_in "-node-local" $@) && $(_in "+node-local" $@) && ! $(_in "+node" $@) ; then
    echo "* installing a local version of node (v$ZDS_NODE_VERSION) & yarn"
    mkdir -p .local
    cd .local

    if [ -d node ]; then # remove previous install
        rm -R node
    fi

    wget -qO https://nodejs.org/dist/v${ZDS_NODE_VERSION}/node-v${ZDS_NODE_VERSION}-linux-x64.tar.xz
    if [[ $? == 0 ]]; then
        tar -xJf node-v${ZDS_NODE_VERSION}-linux-x64.tar.xz
        rm node-v${ZDS_NODE_VERSION}-linux-x64.tar.xz
        mv node-v${ZDS_NODE_VERSION}-linux-x64 node

        # symbolic links to node stuffs in venv
        ln -s $(realpath node/bin/node) ../$ZDS_VENV/bin/
        ln -s $(realpath node/bin/npm) ../$ZDS_VENV/bin/npm
        ln -s $(realpath node/bin/npx) ../$ZDS_VENV/bin/npx
        ln -s $(realpath node/include/node) ../$ZDS_VENV/include/
        ln -s $(realpath node/lib/node_modules) ../$ZDS_VENV/lib/
        ln -s $(realpath node/share/systemtap) ../$ZDS_VENV/share/

        npm -g add yarn
        ln -s $(realpath ./node/bin/yarn) ../$ZDS_VENV/bin/yarn
    else
        echo "!! Cannot find this version of node"
        exit 1;
    fi;
    cd ..
fi

# local elasticsearch
if  ! $(_in "-elasticsearch" $@) && ( $(_in "+elasticsearch" $@) || $(_in "+full" $@) ); then
    echo "* installing a local version of elasticsearch (v$ZDS_ELASTIC_VERSION)"
    mkdir -p .local
    cd .local

    if [ -d elasticsearch ]; then # remove previous install
        rm -R elasticsearch
    fi

    wget -q0 https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ZDS_ELASTIC_VERSION}.zip
    if [[ $? == 0 ]]; then
        unzip elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        rm elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        mv elasticsearch-${ZDS_ELASTIC_VERSION} elasticsearch

        # add options to reduce memory consumption
        echo "#Options added by install_zds.sh" >> elasticsearch/config/jvm.options
        echo "-Xms512m" >> elasticsearch/config/jvm.options
        echo "-Xmx512m" >> elasticsearch/config/jvm.options

        # symbolic link to elastic start script
        ln -s $(realpath elasticsearch/bin/elasticsearch) ../$ZDS_VENV/bin/
    else
        echo "!! Cannot find this version of elasticsearch"
        exit 1;
    fi;
    cd ..
fi

# local texlive
if  ! $(_in "-tex" $@) && ( $(_in "+tex" $@) || $(_in "+full" $@) ); then
    echo "* install template & texlive"

    CURRENT=$(pwd)
    mkdir -p .local
    cd .local
    LOCAL=$CURRENT/.local

    if [ -d texlive ]; then # remove previous install
        rm -Rf texlive
    fi

    # clone
    BASE_TEXLIVE=$LOCAL/texlive
    BASE_REPO=$BASE_TEXLIVE/texmf-local/tex/latex
    mkdir -p $BASE_REPO
    cd $BASE_REPO
    git clone $ZDS_LATEX_REPO

    # copy scripts
    cd $BASE_TEXLIVE
    REPO=$BASE_REPO/latex-template
    cp $REPO/scripts/texlive.profile $REPO/scripts/packages $REPO/scripts/install_font.sh .

    # install fonts
    ./install_font.sh

    # install texlive
    sed -i 's@.texlive@texlive@' texlive.profile  # change directory
    sed -i 's@\$HOME@'"$LOCAL"'@' texlive.profile  # change destination

    wget -O install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
    tar xzf install-tl.tar.gz
    ./install-tl*/install-tl -profile texlive.profile

    ./bin/x86_64-linux/tlmgr install $(cat packages)  # extra packages
    ./bin/x86_64-linux/tlmgr update --self

    # Symlink the binaries to bin of venv
    for i in $BASE_TEXLIVE/bin/x86_64-linux/*; do
      echo $i
      ln -sf $i ../../$ZDS_VENV/bin/
    done

    texhash  # register template

    cd $CURRENT
fi

# install back
if  ! $(_in "-back" $@) && ( $(_in "+back" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* install back dependencies & migration"
    pip3 install --upgrade -r requirements-dev.txt
    make migrate # migration are required for the instance to run properly
fi

# install front
if  ! $(_in "-front" $@) && ( $(_in "+front" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* install front dependencies & build front"
    if [ -d node_modules ]; then # delete previous modules
        rm -R node_modules
    fi;

    yarn
    yarn run build
fi

# zmd
if  ! $(_in "-zmd" $@) && ( $(_in "+zmd" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* install zmarkdown dependencies"
    cd zmd && npm install zmarkdown --production
fi

# fixtures
if  ! $(_in "-data" $@) && ( $(_in "+data" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    echo "* fixtures"
    python manage.py loaddata fixtures/*.yaml
	python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml
fi

echo -n 'Done. You can now run instance with `'
echo -n "source $ZDS_VENV/bin/activate"
echo '`, `and then, `make zmd-start && make run-back`'
