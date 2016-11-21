#!/bin/bash
cd $(dirname $0)
cd ../zds

YAPF_DIFF=$(yapf --diff --recursive --style ../.yapf.style $1)

if [[ $(echo $YAPF_DIFF | wc -c) -ne 1 ]]; then
    echo "Code style checks failed, here's the diff:"
    echo "$YAPF_DIFF"
    exit 1;
else
    echo "Code style is good!"
fi
