#!/bin/bash

# Install script for the zds-site repository


# load nvm
function load_nvm {
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
}


# zds-site root folder
ZDSSITE_DIR=$(pwd)


# variables
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
source $LOCAL_DIR/define_variable.sh
source $LOCAL_DIR/define_function.sh


# Install packages
if  ! $(_in "-packages" $@) && ( $(_in "+packages" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* [+packages] installing packages (this subcommand will be run as super-user)" --bold

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

        if ! [ "$REPLY" -eq "$REPLY" ] 2> /dev/null; then # check $REPLY contains a number
            print_error "!! You have to pick a number!"
            exit 1
        fi

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
fi


# virtualenv

if  ! $(_in "-virtualenv" $@) && ( $(_in "+virtualenv" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* Create virtualenv" --bold

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

        print_info "* [+virtualenv] installing \`virtualenv $ZDS_VENV_VERSION\` with pip"
        pip3 install --user virtualenv==$ZDS_VENV_VERSION

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
    print_info "* [+node] installing nvm (v$ZDS_NVM_VERSION) & node (v$ZDS_NODE_VERSION) & yarn" --bold

    wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v${ZDS_NVM_VERSION}/install.sh | bash
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
fi

# virtualenv activation
if ! $(_in "--force-skip-activating" $@) && [[ ( $VIRTUAL_ENV == "" || $(realpath $VIRTUAL_ENV) != $(realpath $ZDS_VENV) ) ]]; then
    print_info "* Load virtualenv" --bold

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

    # Some dependencies (like rust ones) require a recent pip:
    print_info "* upgrading pip"
    pip install pip==$ZDS_PIP_VERSION; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Failed to upgrade pip"
        exit 1
    fi

    print_info "!! Add \`$(realpath $ZDS_VENV)\` in your PATH."

    if [ ! -d $ZDS_VENV ]; then
        mkdir $ZDS_VENV
    fi
fi

export ZDS_ENV=$(realpath $ZDS_VENV)


# local Typesense
if  ! $(_in "-typesense-local" $@) && ( $(_in "+typesense-local" $@) || $(_in "+full" $@) ); then
    print_info "* [+typesense-local] installing a local version of typesense (v$ZDS_TYPESENSE_VERSION)" --bold

    mkdir -p .local
    cd .local

    readonly typesense_path=$(realpath typesense)

    if [ -d "$typesense_path" ]; then # remove previous install
        rm -r "$typesense_path"
    fi

    mkdir $typesense_path
    cd $typesense_path

    readonly archive_name=typesense-server-$ZDS_TYPESENSE_VERSION-linux-amd64.tar.gz

    wget  -q https://dl.typesense.org/releases/$ZDS_TYPESENSE_VERSION/$archive_name --show-progress
    if [[ $? == 0 ]]; then
        tar -xzf $archive_name
        rm $archive_name
        mkdir typesense-data
    else
        print_error "!! Cannot get typesense ${ZDS_TYPESENSE_VERSION}"
        exit 1
    fi
    cd $ZDSSITE_DIR
fi

# local texlive
if  ! $(_in "-tex-local" $@) && ( $(_in "+tex-local" $@) || $(_in "+full" $@) ); then
    print_info "* [+tex-local] install texlive" --bold

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

        wget -O install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz -q --show-progress
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
fi


# latex-template in TEXMFHOME.
if  ! $(_in "-latex-template" $@) && ( $(_in "+latex-template" $@) || $(_in "+full" $@) ); then
    print_info "* [+latex-template] install latex-template (from $ZDS_LATEX_REPO)" --bold

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
fi


# install back
if  ! $(_in "-back" $@) && ( $(_in "+back" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* [+back] install back dependencies & migration" --bold

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
fi


# zmd (zmd has to be installed before the build the front)
if  ! $(_in "-zmd" $@) && ( $(_in "+zmd" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* [+zmd] install zmarkdown dependencies" --bold

    make zmd-install; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "!! Cannot install zmd (use \`-zmd\` to skip)"
        exit 1
    fi
fi


# install front
if  ! $(_in "-front" $@) && ( $(_in "+front" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* [+front] install front dependencies & build front" --bold

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
fi


# fixtures
if  ! $(_in "-data" $@) && ( $(_in "+data" $@) || $(_in "+base" $@) || $(_in "+full" $@) ); then
    print_info "* [+data] fixtures" --bold

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
fi

if  ! $(_in "--force-skip-activating" $@); then
    print_info "Done. You can now run instance with \`source $ZDS_VENV/bin/activate\`, and then, \`make zmd-start && make run-back\`"
else
    print_info "Done. You can now run instance with \`make zmd-start && make run-back\`"
fi
