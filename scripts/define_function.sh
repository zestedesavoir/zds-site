#!/bin/bash


function _in {
  # credits: https://stackoverflow.com/a/8574392
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}


## travis code
# https://github.com/travis-ci/travis-build/blob/master/lib/travis/build/bash/travis_fold.bash
zds_travis_fold() {
    local action="${1}"
    local name="${2}"
    echo -en "travis_fold:${action}:${name}\\r${ANSI_CLEAR}"
}


# https://github.com/travis-ci/travis-build/blob/master/lib/travis/build/bash/travis_nanoseconds.bash
zds_travis_nanoseconds() {
  local cmd='date'
  local format='+%s%N'

  if hash gdate >/dev/null 2>&1; then
    cmd='gdate'
  elif [[ "${TRAVIS_OS_NAME}" == osx ]]; then
    format='+%s000000000'
  fi

  "${cmd}" -u "${format}"
}


# https://github.com/travis-ci/travis-build/blob/master/lib/travis/build/bash/travis_time_start.bash
# change : prefixed global variable with ZDS_
zds_travis_time_start() {
    ZDS_TRAVIS_TIMER_ID="ZDS_$(printf %08x $((RANDOM * RANDOM)))"
    ZDS_TRAVIS_TIMER_START_TIME="$(zds_travis_nanoseconds)"
    export ZDS_TRAVIS_TIMER_ID ZDS_TRAVIS_TIMER_START_TIME
    echo -en "travis_time:start:${ZDS_TRAVIS_TIMER_ID}\\r${ANSI_CLEAR}"
}


# https://github.com/travis-ci/travis-build/blob/master/lib/travis/build/bash/travis_time_finish.bash
# change : prefixed global variable with ZDS_
zds_travis_time_finish() {
    local result="${?}"
    local travis_timer_end_time
    travis_timer_end_time="$(zds_travis_nanoseconds)"
    local duration
    duration="$((travis_timer_end_time - ZDS_TRAVIS_TIMER_START_TIME))"
    echo -en "travis_time:end:${ZDS_TRAVIS_TIMER_ID}:start=${ZDS_TRAVIS_TIMER_START_TIME},finish=${travis_timer_end_time},duration=${duration}\\r${ANSI_CLEAR}"
    return "${result}"
}
##


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
        zds_travis_fold "start" "${zds_fold_current_cat}_${zds_fold_current}"

        zds_travis_time_start
    fi

    print_info "$2" --bold
}


function zds_fold_end {
    if [[ $ZDS_SHOW_TRAVIS_FOLD == 1 ]] && [[ $zds_fold_current =~ "" ]]; then
        zds_travis_time_finish

        zds_travis_fold "end" "${zds_fold_current_cat}_${zds_fold_current}"
        zds_fold_current=""
    fi
}
## end


## start zmd start & stop function
function zds_start_zmd {
    npm run server --prefix zmd/node_modules/zmarkdown -- --silent; exVal=$?

    if [[ $exVal != 0 ]]; then
        zds_fold_end
        gateway "!! Cannot start zmd" $exVal
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