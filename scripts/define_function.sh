#!/bin/bash


function _in {
  # credits: https://stackoverflow.com/a/8574392
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}


## start fold for travis
ZDS_SHOW_TRAVIS_FOLD=0
if $(_in "--travis-output" $@); then
    ZDS_SHOW_TRAVIS_FOLD=1
fi


zds_fold_current_cat="default"
function zds_fold_category {
    zds_fold_current_cat="$1"
}


zds_fold_current=""
function zds_fold_start {
    if [[ $ZDS_SHOW_TRAVIS_FOLD == 1 ]]; then
        if [[ $zds_fold_current == $1 ]]; then # for virtualenv fold
            return
        fi

        zds_fold_current="$1"
        echo "travis_fold:start:${zds_fold_current_cat}_${zds_fold_current}"
        echo -en "\033[0K"
    fi

    print_info "$2" --bold
}


function zds_fold_end {
    if [[ $ZDS_SHOW_TRAVIS_FOLD == 1 ]] && [[ $zds_fold_current =~ "" ]]; then
        echo "travis_fold:end:${zds_fold_current_cat}_${zds_fold_current}"
        echo -en "\033[0K"
        zds_fold_current=""
    fi
}
## end


## start zmd start & stop function
function zds_start_zmd {
    npm run server --prefix zmd/node_modules/zmarkdown -- --silent; exVal=$?

    if [[ $exVal != 0 ]]; then
        zds_fold_end
        print_error "!! Cannot start zmd"
        exit 1
    fi
}


function zds_stop_zmd {
    pm2 kill; exVal=$?

    if [[ $exVal != 0 ]]; then
        print_error "Warning: Cannot stop zmd"
    fi
}
## end


function gateway {
    if [[ $2 != 0 ]]; then
        print_error "$1"
        exit $2
    fi
}


## start print function
function print_info {
    if [[ "$2" == "--bold" ]]; then
        echo -en "\033[36;1m"
    else
        echo -en "\033[0;36m"
    fi
    echo "$1"
    echo -en "\033[00m"
}


function print_error {
    echo -en "\033[31;1m"
    echo "$1"
    echo -en "\033[00m"
}
## end