#!/bin/bash
#
# Zeste de Savoir deployment script updater
#
# Updates the ZdS deployment script and launch it
#
# Usage:
# - This script must be run by zds user
# - This script has exactly 1 parameter: the tag name to deploy
#

if [ "$(whoami)" != "zds" ]; then
  echo "This script must be run by zds user" >&2
  exit 1
fi

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <tag name>" >&2
  exit 1
fi

echo "Backing up the previous deployment script"
mv -f deploy.sh deploy.sh.bak

echo "Fetching the appropriate version of the deployment script"
wget https://raw.githubusercontent.com/zestedesavoir/zds-site/$1/scripts/deploy.sh
chmod +x deploy.sh

echo "Runing the deployment script…"
./deploy.sh ok $@

