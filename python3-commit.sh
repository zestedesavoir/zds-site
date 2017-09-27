#!/bin/bash

cd "$(dirname "$0")"

./python3.sh

git commit -a -m ':snake: :three:  ·  2to3' -m 'Ce commit a été fait automatiquement par 2to3.'
git revert --no-edit $(git log --oneline --grep='REVERT ME LATER' | cut -f1 -d' ')
