#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir

if [ "$(whoami)" != "zds" ]; then
	echo "This script must be run by zds user" >&2
	exit 1
fi

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <tag name>" >&2
	exit 1
fi
cd /opt/zdsenv/ZesteDeSavoir/

# Switch to new tag
git fetch --tags
# Server has git < 1.9, git fetch --tags doesn't retrieve commits...
git fetch
# -b is required to have version data in footer
git checkout -b $1

# Compute front stuff
source /usr/local/nvm/nvm.sh
gulp pack

# Update application data
source ../bin/activate
pip install --upgrade -r requirements.txt
python manage.py migrate
deactivate

# Restart zds
sudo supervisorctl restart zds
