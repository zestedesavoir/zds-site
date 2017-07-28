#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir
#
# DON'T RUN THIS SCRIPT DIRECTLY
# Running update_and_deploy.sh <tag> instead will first get the
# appropriate version of this script and run it instead.

set -euo pipefail
IFS=$'\n\t'

ENV_PATH="/opt/zds/zdsenv"
REPO_PATH="/opt/zds/zds-site"

if [ "$1" != "ok" ]; then
  echo "This script shouldn't be run directly. Run ./update_and_deploy.sh <tag> instead." >&2
  exit 1
fi

# Shift the first arg "ok"
shift

if [ "$(whoami)" != "zds" ]; then
  echo "This script must be run by zds user" >&2
  exit 1
fi

# Check if the git working directory is clean (excluding scripts/ folder)
if ! git diff-index --quiet HEAD -- . ':!scripts/'; then
  echo "Git repo has uncommited changes. Make sure it's clean before trying again" >&2
  exit 1
fi

read -p "Did you run specific tasks for this version as described in update.md? [y/N] " -r
echo  # move to a new line

if [[ ! $REPLY =~ ^[Yy]$ ]] then
  echo "Do it, now!"
  exit 1
fi

cd $REPO_PATH

# Enable maintenance mode
sudo ln -sf errors/maintenance.html $ENV_PATH/webroot/

# Delete old branch if exists
git checkout refs/heads/prod

if git rev-parse --verify "refs/heads/$1" > /dev/null; then
  git branch -D $1
fi

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
git checkout refs/heads/$1-build
# Create a branch with the same name - required to have version data in footer
git checkout -b $1

# Update application data
source $ENV_PATH/bin/activate
pip install --upgrade -r requirements-prod.txt
python manage.py migrate
python manage.py compilemessages

## Collect all staticfiles from dist/ and python packages to static/
python manage.py collectstatic --noinput --clear
## Exit venv
deactivate

# Restart zds
sudo systemctl restart zds.{service,socket}

# Clean the cache by restarting it
sudo service memcached restart

# Disable maintenance mode
sudo rm $ENV_PATH/webroot/maintenance.html

# update latex
mkdir -p $HOME/texmf/tex/latex/
wget "https://raw.githubusercontent.com/zestedesavoir/latex-template/${1-build}/zmdocument.cls"
mv zmdocument.cls $HOME/texmf/tex/latex/
sudo texhash
# Display current branch and commit
git status
echo "Deployed commit: `git rev-parse HEAD`"
echo "Dont forget to run specific tasks for this version as described in update.md"
