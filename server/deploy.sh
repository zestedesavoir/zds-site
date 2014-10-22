#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir
#
# Usage:
# - This script must be run by zds user
# - This script has exactly 1 parameter: the tag name to deploy

if [ "$(whoami)" != "zds" ]; then
	echo "This script must be run by zds user" >&2
	exit 1
fi

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <tag name>" >&2
	exit 1
fi

read -p "Did you run specific tasks for this version as described in update.md? " -r
echo    # move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
	echo "Do it, now!"
	exit 1
fi

cd /opt/zdsenv/ZesteDeSavoir/

# Maintenance mode
sudo rm /etc/nginx/sites-enabled/zestedesavoir
sudo ln -s /etc/nginx/sites-available/zds-maintenance /etc/nginx/sites-enabled/zds-maintenance
sudo service nginx reload

# Delete old branch if exists
git checkout prod
git branch -D $1
# Switch to new tag
git fetch --tags
# Server has git < 1.9, git fetch --tags doesn't retrieve commits...
git fetch
# Checkout the tag
git checkout $1
# Create a branch with the same name - required to have version data in footer
git checkout -b $1

# Compute front stuff
source /usr/local/nvm/nvm.sh
sudo npm -q update
sudo npm -q update bower gulp -g
gulp pack

# Update application data
source ../bin/activate
pip install --upgrade --use-mirrors -r requirements.txt
python manage.py migrate
deactivate

# Restart zds
sudo supervisorctl restart zds

# Exit maintenance mode
sudo rm /etc/nginx/sites-enabled/zds-maintenance
sudo ln -s /etc/nginx/sites-available/zestedesavoir /etc/nginx/sites-enabled/zestedesavoir
sudo service nginx reload

# Display current branch and commit
git status
echo "Commit deployé : `git rev-parse HEAD`"
