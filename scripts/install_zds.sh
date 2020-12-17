#!/bin/bash

# Install script for the zds-site repository


# load nvm
function load_nvm {
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
}


## start quiet mode
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
## end


# zds-site root folder
ZDSSITE_DIR=$(pwd)


# variables
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
source $LOCAL_DIR/define_variable.sh
source $LOCAL_DIR/define_function.sh

zds_fold_category "install"


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
            print_error "!! Please manually install the packages and run again without \`--detect-os-version\`"
            exit 1
        fi
    else
        echo -en "\033[33;1m";
        n=1
        arr=()

        for filepath in $LOCAL_DIR/dependencies/*.txt; do
            title=$(grep -oP '#title=\K(.*)' "$filepath")
            desc=$(grep -oP '#desc=\K(.*)' "$filepath")
            echo "$n. $title - $desc"
            arr[n]=$filepath
            ((n++))
        done

        echo -en "\033[00m"

        echo -n "Choice : "
        read -n 1
        echo ""

        filepath="${arr[$REPLY]}"
        if [[ $filepath == "" ]]; then
            print_error "!! You don't pick the right choice."
            exit 1
        fi
    fi
    echo ""

    packagingTool_update=$(grep -oP '#updatecmd=\K(.*)' "$filepath")
    packagingTool_install=$(grep -oP '#installcmd=\K(.*)' "$filepath")
    print_info "$filepath"
    IFS=$'\n'

    if [[ $packagingTool_update ]]; then
        print_info "sudo $packagingTool_update"
        echo ""
        eval "sudo $packagingTool_update"; exVal=$?
        echo ""
        if [[ $exVal != 0 ]]; then
            print_error "!! We were unable to update packages list."
        fi
    fi

    for dep in $(cat "$filepath"); do
        if [[ $dep == "#"* ]]; then
            continue;
        fi

        print_info "sudo $packagingTool_install $dep"
        echo ""
        eval "sudo $packagingTool_install $dep"; exVal=$?
        echo ""

        if [[ $exVal != 0 && $dep == "python3-venv" ]]; then
            print_error "!! We were unable to install virtualenv. Don't panic, we will try with pip3."
        elif [[ $exVal != 0 && ! $(_in "--answer-yes" $@) ]]; then
            print_error "Unable to install \`$dep\`, press \`y\` to continue the script."
            echo -n "Choice : "
            read -n 1
            echo ""
            if [[ $REPLY == "y" ]]; then
                print_info "Installation continued"
            else
                print_error "!! Installation aborted"
                exit 1
            fi
        elif [[ $exVal != 0 && $(_in "--answer-yes" $@) ]]; then
            print_info "Installation continued (auto answer: \`yes\`)."
        else
            print_info "$dep: success."
        fi
        echo ""
    done

    zds_fold_end
fi


# virtualenv

if  ! $(_in "-virtualenv" $@) && ( $(_in "+virtualenv" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "virtualenv" "* Create virtualenv"

    if [ ! -f $ZDS_VENV/bin/activate ]; then
        if [ -d $ZDS_VENV ]; then
            print_info "!! Find corrupted virtualenv folder without bin/activate"

            if $(_in "--answer-yes" $@); then
                print_info "remove $(realpath $ZDS_VENV)"
                rm -r $ZDS_VENV
            else
                print_error "We recommend to delete this folder, press \`y\` to delete this folder"
                echo -n "Choice : "
                read -n 1
                echo ""
                if [[ $REPLY == "y" ]]; then
                    print_info "remove $(realpath $ZDS_VENV)"
                    rm -r $ZDS_VENV
                else
                    print_error "!! Cannot continue. Move, rename or delete this folder before retry"
                    exit 1
                fi
            fi
        fi

        print_info "* [+virtualenv] installing \`virtualenv 16.2.0\` with pip"
        pip3 install --user virtualenv==16.2.0

        print_info "* [+virtualenv] creating virtualenv"
        err=$(python3 -m venv $ZDS_VENV 3>&1 1>&2 2>&3 | sudo tee /dev/stderr)
        if [[ $err != "" ]]; then
            exVal=1
            if [[ $err == *"ensurepip"* ]]; then # possible issue on python 3.6
                print_info "!! Trying to create the virtualenv without pip"
                python3 -m venv $ZDS_VENV --without-pip; exVal=$?
            fi

            if [[ $exVal != 0 ]]; then
                print_error "!! Cannot create (use \`-virtualenv\` to skip)"
                print_info "You can try to change the path of zdsenv folder before retrying this command with \`export ZDS_VENV=../zdsenv\`"
                exit 1
            fi
        fi
    fi
fi

# nvm node & yarn
if  ! $(_in "-node" $@) && ( $(_in "+node" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "node" "* [+node] installing nvm (v$ZDS_NVM_VERSION) & node (v$ZDS_NODE_VERSION) & yarn"

    wget -qO- https://raw.githubusercontent.com/creationix/nvm/v${ZDS_NVM_VERSION}/install.sh | bash
    if [[ $? == 0 ]]; then

        # load nvm
        load_nvm

        # install node (using .nvmrc implicitly) & yarn
        nvm install
        npm -g add yarn

        if [[ $(grep -c -i "nvm use" $ZDS_VENV/bin/activate) == "0" ]]; then # add nvm activation to venv activate's
            ACTIVATE_NVM="nvm use > /dev/null # activate nvm (from install_zds.sh)"

            echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate
            echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate.csh
            echo $ACTIVATE_NVM >> $ZDS_VENV/bin/activate.fish
        fi
    else
        print_error "!! Cannot obtain nvm v${ZDS_NVM_VERSION}"
        exit 1
    fi

    zds_fold_end
fi

# virtualenv activation
if ! $(_in "--force-skip-activating" $@) && [[ ( $VIRTUAL_ENV == "" || $(realpath $VIRTUAL_ENV) != $(realpath $ZDS_VENV) ) ]]; then
    zds_fold_start "virtualenv" "* Load virtualenv"

    print_info "* activating venv \`$ZDS_VENV\`"

    if [ -d $HOME/.nvm ]; then # load nvm, in case of
        load_nvm
    fi

    if [ ! -f $ZDS_VENV/bin/activate ]; then
        echo ""
        print_error "!! No virtualenv, cannot continue"
        print_info "   - Install virtualenv with \`+virtualenv\` (recommanded) ;"
        echo "   - If you don't have other choice, use \`--force-skip-activating\`."
        exit 1
    fi

    source $ZDS_VENV/bin/activate; exVal=$?

    if [[ $exVal != 0 ]]; then
        echo ""
        print_error "!! Cannot load virtualenv"
        print_info "   - Reinstall virtualenv with \`+virtualenv\` (recommanded) ;"
        echo "   - If you don't have other choice, use \`--force-skip-activating\`."
        exit 1
    fi

    zds_fold_end
else 
    print_info "!! Add \`$(realpath $ZDS_VENV)\` in your PATH."

    if [ ! -d $ZDS_VENV ]; then
        mkdir $ZDS_VENV
    fi

    zds_fold_end
fi

export ZDS_ENV=$(realpath $ZDS_VENV)


# local jdk 
if  ! $(_in "-jdk-local" $@) && ( $(_in "+jdk-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "jdk" "* [+jdk-local] installing a local version of JDK (v$ZDS_JDK_VERSION)"

    mkdir -p $ZDS_VENV/lib/
    cd $ZDS_VENV/lib/

    jdk_path=$(realpath jdk)

    if [ -d "$jdk_path" ]; then # remove previous install
        rm -rf "$jdk_path"
    fi

    baseURL="https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/"
    foldername="jdk-${ZDS_JDK_VERSION}+${ZDS_JDK_REV}"
    folderPATH="${foldername}/OpenJDK11U-jdk_x64_linux_hotspot_${ZDS_JDK_VERSION}_${ZDS_JDK_REV}.tar.gz"

    echo "GET ${baseURL}${folderPATH}"
    wget_nv -O ${foldername}.tar.gz ${baseURL}${folderPATH}
    tar xf ${foldername}.tar.gz

    if [[ $? == 0 ]]; then
        rm ${foldername}.tar.gz
        mv ${foldername} "$jdk_path"

        echo $($jdk_path/bin/java -version)

        export PATH="$PATH:$jdk_path/bin"
        export JAVA_HOME="$jdk_path"
        export ES_JAVA_OPTS="-Xms512m -Xmx512m"

        if [[ $(grep -c -i "export JAVA_HOME" $ZDS_ENV/bin/activate) == "0" ]]; then # add java to venv activate's
            ACTIVATE_JAVA="export PATH=\"\$PATH:$jdk_path/bin\"\nexport JAVA_HOME=\"$jdk_path\"\nexport ES_JAVA_OPTS=\"-Xms512m -Xmx512m\""

            echo -e $ACTIVATE_JAVA >> $ZDS_ENV/bin/activate
            echo -e $ACTIVATE_JAVA >> $ZDS_ENV/bin/activate.csh
            echo -e $ACTIVATE_JAVA >> $ZDS_ENV/bin/activate.fish
        fi
    else
        print_error "!! Cannot get or extract jdk ${ZDS_JDK_VERSION}"
        exit 1
    fi
    cd $ZDSSITE_DIR

    zds_fold_end
fi


# local elasticsearch
if  ! $(_in "-elastic-local" $@) && ( $(_in "+elastic-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "elasticsearch" "* [+elastic-local] installing a local version of elasticsearch (v$ZDS_ELASTIC_VERSION)"

    mkdir -p .local
    cd .local

    es_path=$(realpath elasticsearch)

    if [ -d "$es_path" ]; then # remove previous install
        rm -r "$es_path"
    fi

    wget_nv https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ZDS_ELASTIC_VERSION}.zip
    if [[ $? == 0 ]]; then
        unzip -q elasticsearch-${ZDS_ELASTIC_VERSION}.zip 
        rm elasticsearch-${ZDS_ELASTIC_VERSION}.zip
        mv elasticsearch-${ZDS_ELASTIC_VERSION} elasticsearch

        # add options to reduce memory consumption
        print_info "#Options added by install_zds.sh" >> "$es_path/config/jvm.options"
        print_info "-Xms512m" >> "$es_path/config/jvm.options"
        print_info "-Xmx512m" >> "$es_path/config/jvm.options"

        # symbolic link to elastic start script
        ln -s "$es_path/bin/elasticsearch" $ZDS_ENV/bin/
    else
        print_error "!! Cannot get elasticsearch ${ZDS_ELASTIC_VERSION}"
        exit 1
    fi
    cd $ZDSSITE_DIR

    zds_fold_end
fi


# local texlive
if  ! $(_in "-tex-local" $@) && ( $(_in "+tex-local" $@) || $(_in "+full" $@) ); then
    zds_fold_start "texlive" "* [+tex-local] install texlive"

    mkdir -p .local
    cd .local
    LOCAL=$ZDSSITE_DIR/.local

    # clone
    BASE_REPO=$LOCAL/texlive
    REPO=$BASE_REPO/latex-template

    mkdir -p $BASE_REPO
    cd $BASE_REPO

    if [ -d $REPO ]; then # remove previous version of the template
        rm -rf $REPO
    fi

    git clone $ZDS_LATEX_REPO
    if [[ $? == 0 ]]; then
        # copy scripts
        cd $BASE_REPO
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
                for i in $BASE_REPO/bin/x86_64-linux/*; do
                  ln -sf $i $ZDS_ENV/bin/
                done
            fi

            ./bin/x86_64-linux/tlmgr install $(cat packages)  # extra packages
            ./bin/x86_64-linux/tlmgr update --self

            # Install tabu-fixed packages
            mkdir -p $BASE_REPO/texmf-local/tex/latex/tabu
            wget -P $BASE_REPO/texmf-local/tex/latex/tabu https://raw.githubusercontent.com/tabu-issues-for-future-maintainer/tabu/master/tabu.sty

            rm -rf $REPO
        else
            print_error "!! Cannot download texlive"
            exit 1
        fi
    else
        print_error "!! Cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $ZDSSITE_DIR

    zds_fold_end
fi


# latex-template in TEXMFHOME.
if  ! $(_in "-latex-template" $@) && ( $(_in "+latex-template" $@) || $(_in "+full" $@) ); then
    zds_fold_start "latex-template" "* [+latex-template] install latex-template (from $ZDS_LATEX_REPO)"

    if [[ $(which kpsewhich) == "" ]]; then # no texlive ?
        print_error "!! Cannot find kpsewhich, do you have texlive?"
        exit 1;
    fi

    # clone
    BASE_REPO=$(kpsewhich -var-value TEXMFHOME)/tex/latex
    REPO=$BASE_REPO/latex-template

    if [ -d $REPO ]; then # remove previous version of the template
        rm -rf $REPO
    fi

    mkdir -p $BASE_REPO
    cd $BASE_REPO

    git clone $ZDS_LATEX_REPO
    if [[ $? != 0 ]]; then
        print_error "!! Cannot clone repository $ZDS_LATEX_REPO"
        exit 1
    fi

    cd $ZDSSITE_DIR

    zds_fold_end
fi


# install back
if  ! $(_in "-back" $@) && ( $(_in "+back" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "back" "* [+back] install back dependencies & migration"

    if $(_in "+prod" $@); then
        make install-back-with-prod; exVal=$?
    else
        make install-back; exVal=$?
    fi

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot install back dependencies (use \`-back\` to skip)"
        exit 1
    fi

    if ! $(_in "-back-migrate-db" $@); then
        make migrate-db; exVal=$? # migration are required for the instance to run properly anyway

        if [[ $exVal != 0 ]]; then
            print_error "!! Cannot migrate database after the back installation (use \`-back\` to skip)"
            exit 1
        fi
    fi

    zds_fold_end
fi


# install front
if  ! $(_in "-front" $@) && ( $(_in "+front" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "front" "* [+front] install front dependencies & build front"

    if [ -d node_modules ]; then # delete previous modules
        rm -r node_modules
    fi

    make install-front; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot install-front (use \`-front\` to skip)"
        exit 1
    fi

    make build-front; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot build-front (use \`-front\` to skip)"
        exit 1
    fi

    zds_fold_end
fi


# zmd
if  ! $(_in "-zmd" $@) && ( $(_in "+zmd" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "zmd" "* [+zmd] install zmarkdown dependencies"

    make zmd-install; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot install zmd (use \`-zmd\` to skip)"
        exit 1
    fi

    zds_fold_end
fi


# fixtures
if  ! $(_in "-data" $@) && ( $(_in "+data" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    zds_fold_start "fixtures" "* [+data] fixtures"

    npm run server --prefix zmd/node_modules/zmarkdown -- --silent; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot start zmd to generate-fixtures (use \`-data\` to skip)"
        exit 1
    fi

    # We check if ZMD is really up:
    nb_zmd_try=0

    while ! curl -s $ZMD_URL > /dev/null && [ $nb_zmd_try -lt 40 ]
    do
        sleep 0.2
        nb_zmd_try=$(($nb_zmd_try+1))
    done

    if [ $nb_zmd_try -eq 40 ]
    then
        print_error "!! Cannot connect to zmd to generate-fixtures (use \`-data\` to skip)"
        exit 1
    fi

    python manage.py loaddata fixtures/*.yaml; exVal=$?
    python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml; exVal=($exVal + $?)
    python manage.py load_fixtures --size=low --all; exVal=($exVal + $?)

    futureExit=false
    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot generate-fixtures (use \`-data\` to skip)"
        futureExit=true
        # don't exit here, because we have to stop zmd !
    fi

    make zmd-stop; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "Warning: Cannot stop zmd"

    fi

    if $futureExit; then
        exit 1
    fi

    zds_fold_end
fi

if  ! $(_in "--force-skip-activating" $@); then
    print_info "Done. You can now run instance with \`source $ZDS_VENV/bin/activate\`, and then, \`make zmd-start && make run-back\`"
else
    print_info "Done. You can now run instance with \`make zmd-start && make run-back\`"
fi
