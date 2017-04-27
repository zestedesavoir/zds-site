#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir
#
# Usage:
# - This script must be run by zds user
# - This script has exactly 1 parameter: the tag name to deploy

ENV_PATH="/opt/zds/zdsenv"
REPO_PATH="/opt/zds/zds-site"

if [ "$(whoami)" != "zds" ]; then
	echo "This script must be run by zds user" >&2
	exit 1
fi

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <tag name>" >&2
	exit 1
fi

read -p "Did you run specific tasks for this version as described in update.md? [y/N] " -r
echo    # move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
	echo "Do it, now!"
	exit 1
fi

cd $REPO_PATH

# Maintenance mode
sudo ln -s errors/maintenance.html $ENV_PATH/webroot/

# Delete old branch if exists
git checkout prod
git branch -D $1
# Removes dist/ folder to avoid conflicts
rm -rf ./dist/
# Switch to new tag
git fetch --tags
# Server has git < 1.9, git fetch --tags doesn't retrieve commits...
git fetch

if git rev-parse $1 >/dev/null 2>&1
then
	echo "Tag $1 found!"
else
	echo "Tag $1 doesn't exist."
	exit 1;
fi

# Checkout the tag
git checkout $1-build
# Create a branch with the same name - required to have version data in footer
git checkout -b $1

# Update application data
source $ENV_PATH/bin/activate
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-prod.txt
python manage.py migrate
python manage.py compilemessages
# Collect all staticfiles from dist/ and python packages to static/
python manage.py collectstatic --noinput --clear
deactivate

# Restart zds
sudo systemctl restart zds.{service,socket}

# clean the cache by restarting it
sudo service memcached restart

# Exit maintenance mode
sudo rm $ENV_PATH/webroot/maintenance.html

# Display current branch and commit
git status
echo "Deployed commit: `git rev-parse HEAD`"
echo "Dont forget to run specific tasks for this version as described in update.md"
