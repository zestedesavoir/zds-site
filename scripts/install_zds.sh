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

# >>>>>
ZDS_SHOW_TRAVIS_FOLD=0
if $(_in "--travis-output" $@); then
    ZDS_SHOW_TRAVIS_FOLD=1
fi

zds_fold_current=""
function zds_fold_start {
    if [[ $ZDS_SHOW_TRAVIS_FOLD == 1 ]]; then
        if [[ $zds_fold_current == $1 ]]; then # for virtualenv fold
            return
        fi

        zds_fold_current="$1"
        echo "travis_fold:start:install_${zds_fold_current}"
        echo -en "\033[0K"; 
    fi

    print_info "$2" --bold
}

function zds_fold_end {
    if [[ $ZDS_SHOW_TRAVIS_FOLD == 1 ]] && [[ $zds_fold_current =~ "" ]]; then
        echo "travis_fold:end:install_${zds_fold_current}"
        echo -en "\033[0K"; 
        zds_fold_current=""
    fi
}
# <<<<<


function print_info {
    if [[ "$2" == "--bold" ]]; then
        echo -en "\033[36;1m";
    else
        echo -en "\033[0;36m";
    fi
    echo "$1";
    echo -en "\033[00m";
}


function print_error {
    echo -en "\033[31;1m";
    echo "$1";
    echo -en "\033[0m";
}


# >>>>>
function progressfilt {
    local flag=false c count cr=$'\r' nl=$'\n'
    while IFS='' read -d '' -rn 1 c
    do
        if $flag; then
            printf '%s' "$c"
        else
            if [[ $c != $cr && $c != $nl ]]; then
                count=0
            else
                ((count++))
                if ((count > 1)); then
                    flag=true
                fi
            fi
        fi
    done
}

# Hack for "-q --show-progress" (at least v1.16) and travis uses (travis uses wget 1.15)
function wget_nv {
    wget "$@" --progress=bar:force 2>&1 | progressfilt
}
# <<<<<

# lastSTDERR=""
# Store error of an command, example : `lookafter "sudo apt-get -qq -y install aaaaaaaa"`
# function lookafter {
#     lastSTDERR=$($@ 3>&1 1>&2 2>&3 | sudo tee /dev/stderr)
# }

# variables
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
source $LOCAL_DIR/define_variable.sh

print_info "ok"

# Install packages
if  ! $(_in "-packages" $@) && ( $(_in "+packages" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "packages" "* [+packages] installing packages (this subcommand will be run as super-user)"

    if $(_in "--detect-os-version" $@); then
        version=$(cat /proc/version)

        if [[ "$version" =~ "ubuntu" ]]; then
            filepath="$LOCAL_DIR/dependencies/ubuntu.txt"
        elif [[ "$version" =~ "debian" ]]; then
            filepath="$LOCAL_DIR/dependencies/debian.txt"
        elif [[ "$version" =~ "fedora" ]]; then
            filepath="$LOCAL_DIR/dependencies/fedora.txt"
        elif [[ "$version" =~ "arch" ]]; then
            filepath="$LOCAL_DIR/dependencies/arch.txt"
        else
            print_error "!! I did not detect your linux version"
            print_error "!! Please manually install the packages and run again without `--detect-os-version`"
            exit 1
        fi
    else
        echo -en "\033[33;1m";
        n=1
        arr=()

        for filepath in $LOCAL_DIR/dependencies/*.txt; do
            title=$(grep -oP '#title=\K(.*)' $filepath)
            desc=$(grep -oP '#desc=\K(.*)' $filepath)
            echo "$n. $title - $desc"
            arr[n]=$filepath
            ((n++))
        done

        echo -en "\033[00m"
        echo -n "Choix : "
        read -n 1
        echo ""

        filepath=${arr[$REPLY]}
        if [[ $filepath == "" ]]; then
            print_error "!! You don't pick the right choice."
            exit 1
        fi
    fi;

    packagingTool_install=$(grep -oP '#installcmd=\K(.*)' $filepath)
    print_info "$filepath"
    IFS=$'\n'

    for dep in $(cat $filepath); do
        if [[ $dep == "#"* ]]; then
            continue;
        fi

        print_info "sudo $packagingTool_install $dep"
        echo " "
        eval "sudo $packagingTool_install $dep"

        exVal=$?
        if [[ $exVal > 0 && $dep == "python3-venv" ]]; then
            print_info "!! We were unable to install virtualenv with apt-get. We try to install virtualenv with pip."
            pip install virtualenv
        elif [[ $exVal > 0 && ! $(_in "--answer-yes" $@) ]]; then
            print_error "\`$dep\` not found, press \`y\` to continue the script."
            read -n 1
            echo ""
            if [ "$REPLY" == "y" ]; then
                print_info "Continue installation"
            else
                print_error "Abort installation"
                exit 1
            fi
        elif [[ $exVal > 0 && $(_in "--answer-yes" $@) ]]; then
            print_info "Continue installation (auto answer yes)."
        else
            echo " "
            print_info "$dep: success."
            echo " "
        fi
    done

    zds_fold_end
fi

# virtualenv
if  ! $(_in "-virtualenv" $@) && ( $(_in "+virtualenv" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "virtualenv" "* Load virtualenv"

    print_info "* [+virtualenv] installing \`virtualenv 16.2.0\` with pip"
    pip install virtualenv==16.2.0

    if [ ! -d $ZDS_VENV ]; then
        print_info "* [+virtualenv] creating virtualenv"
        msg=$(python3 -m venv $ZDS_VENV)
        if [[ $? != "0" && $msg == *"ensurepip"* ]]; then
            echo $msg
            print_info "!! Try --without-pip"
            python3 -m venv $ZDS_VENV --without-pip
        elif [[ $? != "0" ]]; then
            echo $msg
        fi
    fi
fi

if [[ $VIRTUAL_ENV == "" || $(basename $VIRTUAL_ENV) != $ZDS_VENV ]]; then
    zds_fold_start "virtualenv" "* Load virtualenv"

    print_info "* activating venv \`$ZDS_VENV\`"

    if [ -d $HOME/.nvm ]; then # force nvm activation, in case of
        _nvm
    fi

    source ./$ZDS_VENV/bin/activate

    if [[ $? != "0" ]]; then
        print_error "!! no virtualenv, cannot continue"
        exit 1
    fi

    zds_fold_end
else 
    zds_fold_end
fi


# nvm node & yarn
if  ! $(_in "-node" $@) && ( $(_in "+node" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "node" "* [+node] installing nvm (v$ZDS_NVM_VERSION) & node (v$ZDS_NODE_VERSION) & yarn"

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
        print_error "!! Cannot obtain nvm v${ZDS_NVM_VERSION}"
        exit 1
    fi

    zds_fold_end
fi


# local jdk 
if  ! $(_in "-jdk-local" $@) && ( $(_in "+jdk-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "jdk" "* [+jdk-local] installing a local version of JDK (v$ZDS_JDK_VERSION)"

    mkdir -p zdsenv/lib/
    cd zdsenv/lib/

    if [ -d jdk ]; then # remove previous install
        rm -R jdk
    fi

    baseURL="https://download.oracle.com/otn-pub/java/jdk/"
    foldername="jdk-${ZDS_JDK_VERSION}"
    folderPATH="${ZDS_JDK_VERSION}${ZDS_JDK_REV}/${ZDS_JDK_HASH}/${foldername}_linux-x64_bin.tar.gz"

    echo "GET ${baseURL}${folderPATH}"
    wget_nv -O ${foldername}.tar.gz --header "Cookie: oraclelicense=accept-securebackup-cookie" ${baseURL}${folderPATH}

    if [[ $? == 0 ]]; then
        tar xf ${foldername}.tar.gz
        rm ${foldername}.tar.gz
        mv ${foldername} jdk

        echo $(./jdk/bin/java --version)

        export PATH="$PATH:$(pwd)/jdk/bin"
        export JAVA_HOME="$(pwd)/jdk"
        export ES_JAVA_OPTS="-Xms512m -Xmx512m"
    else
        print_error "!! Cannot get jdk ${JDK_VERSION}"
        exit 1
    fi
    cd ../../

    zds_fold_end
fi


# local elasticsearch
if  ! $(_in "-elastic-local" $@) && ( $(_in "+elastic-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "elasticsearch" "* [+elastic-local] installing a local version of elasticsearch (v$ZDS_ELASTIC_VERSION)"

    mkdir -p .local
    cd .local

    if [ -d elasticsearch ]; then # remove previous install
        rm -R elasticsearch
    fi

    wget_nv https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ZDS_ELASTIC_VERSION}.zip
    if [[ $? == 0 ]]; then
        unzip -q elasticsearch-${ZDS_ELASTIC_VERSION}.zip 
        rm elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        mv elasticsearch-${ZDS_ELASTIC_VERSION} elasticsearch

        # add options to reduce memory consumption
        print_info "#Options added by install_zds.sh" >> elasticsearch/config/jvm.options
        print_info "-Xms512m" >> elasticsearch/config/jvm.options
        print_info "-Xmx512m" >> elasticsearch/config/jvm.options

        # symbolic link to elastic start script
        ln -s elasticsearch/bin/elasticsearch $VIRTUAL_ENV/bin/
    else
        print_error "!! Cannot get elasticsearch ${ZDS_ELASTIC_VERSION}"
        exit 1;
    fi;
    cd ..

    zds_fold_end
fi


# local texlive
if  ! $(_in "-tex-local" $@) && ( $(_in "+tex-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "texlive" "* [+tex-local] install texlive"

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

        wget_nv -O install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
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
            print_error "!! Cannot download texlive"
            exit 1
        fi
    else
        print_error "!! cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $CURRENT

    zds_fold_end
fi


# latex-template in TEXMFHOME.
if  ! $(_in "-latex-template" $@) && ( $(_in "+latex-template" $@) || $(_in "+full" $@) ); then
    zds_fold_start "latex-template" "* [+latex-template] install latex-template (from $ZDS_LATEX_REPO)"

    CURRENT=$(pwd)

    if [[ $(which kpsewhich) == "" ]]; then # no texlive ?
        print_error "!! Cannot find kpsewhich, do you have texlive?"
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
        print_error "!! cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $CURRENT

    zds_fold_end
fi


# install back
if  ! $(_in "-back" $@) && ( $(_in "+back" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "back" "* [+back] install back dependencies & migration"

    if $(_in "+prod" $@); then
        make install-back-with-prod
    else
        make install-back
    fi
    make migrate-db # migration are required for the instance to run properly anyway

    zds_fold_end
fi


# install front
if  ! $(_in "-front" $@) && ( $(_in "+front" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "front" "* [+front] install front dependencies & build front"

    if [ -d node_modules ]; then # delete previous modules
        rm -R node_modules
    fi;

    make install-front
    make build-front

    zds_fold_end
fi


# zmd
if  ! $(_in "-zmd" $@) && ( $(_in "+zmd" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "zmd" "* [+zmd] install zmarkdown dependencies"

    make zmd-install

    zds_fold_end
fi


# fixtures
if  ! $(_in "-data" $@) && ( $(_in "+data" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "fixtures" "* [+data] fixtures"

    make generate-fixtures

    zds_fold_end
fi


print_info "Done. You can now run instance with \`source $ZDS_VENV/bin/activate\`, and then, \`make zmd-start && make run-back\`"
