## start fold for travis
ZDS_SHOW_TRAVIS_FOLD=0
if $(_in "--travis-output" $@); then
    ZDS_SHOW_TRAVIS_FOLD=1
fi


zds_fold_current_cat="default"
function zds_fold_category {
    zds_fold_category="$1"
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
