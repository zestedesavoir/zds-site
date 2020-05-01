#!/bin/bash

LOCALDIR=$(dirname "$0")
cd $LOCALDIR
source ../define_function.sh

# FOR LOCAL USAGE:
# TRAVIS_JOB_WEB_URL="https://travis-ci.com/github/zestedesavoir/zds-site/jobs/123456789"
# TRAVIS_JOB_ID=$(echo "$TRAVIS_JOB_WEB_URL" 2>&1 | sed -E "s/^.+\/([0-9]+)$/\1/")

if [ -z $TRAVIS_JOB_ID ]; then
  echo "Error: TRAVIS_JOB_ID missing."
  exit 1
fi

echo "https://api.travis-ci.com/v3/job/$TRAVIS_JOB_ID/log.txt"

# 1) get log
curl --silent "https://api.travis-ci.com/v3/job/$TRAVIS_JOB_ID/log.txt" --output log4.txt

# 2) sed will parse log.txt to get the good line number (like in travis-ci.com UI)
sed --in-place log4.txt --regexp-extended --file=sed_parsing_rules.txt

# 3) get the line number
cat log4.txt --number > log3.txt

# 4) Ignore line
grep --invert-match --file="grep_ignore_msg.txt" log3.txt > log2.txt

if [ ! -s log3.txt ]; then
  echo "Error: Should be not empty!"
  exit 1
fi

# 5) Match line with "error" or "Traceback" (and get +5/-5 lines)
grep "\(error\|Traceback\)" log2.txt --color=always --after-context=5 --before-context=5 > log.txt

# 6) Display :
if [ -s log.txt ]; then
  echo "#######################################################"
  echo "      WE FOUND LINES WITH 'error' OR 'traceback'       "
  echo "Scans previous output & prints lines containing 'error'"
  echo "or 'traceback'. Be careful with false positives.       "
  echo "#######################################################"
  zds_fold_start "line-overview" "Lines found"
    cat log.txt | cut --bytes=1-312
  zds_fold_end
  echo "#######################################################"
  echo "                      END                              "
  echo "#######################################################"
fi

rm log2.txt log3.txt log4.txt
