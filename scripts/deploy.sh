#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir
#
# Usage:
# - This script must be run by zds user
# - This script has exactly 1 parameter: the tag name to deploy

: ${ZDS_USER:="zds"}
: ${VIRTUALENV_PATH:=/opt/zdsenv}
: ${APP_PATH:=/opt/zdsenv/ZesteDeSavoir}
: ${NGINX_CONFIG_ROOT:=/etc/nginx}
: ${NGINX_MAINTENANCE_SITE:=zds-maintenance}
: ${NGINX_APP_SITE:=zestedesavoir}
: ${ENABLE_MAINTENANCE:=true}

if [ "$(whoami)" != $ZDS_USER ]; then
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

echo "Here is the config:"
echo "  VIRTUALENV_PATH = $VIRTUALENV_PATH"
echo "  APP_PATH = $APP_PATH"
echo "  NGINX_CONFIG_ROOT = $NGINX_CONFIG_ROOT"
echo "  NGINX_MAINTENANCE_SITE = $NGINX_MAINTENANCE_SITE"
echo "  NGINX_APP_SITE = $NGINX_APP_SITE"
echo "  ENABLE_MAINTENANCE = $ENABLE_MAINTENANCE"
read -p "Is this OK ? [y/N] " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
	echo "You can change these by setting environment variables."
	exit 1
fi

function enable_maintenance {
	sudo rm -I $NGINX_CONFIG_ROOT/sites-enabled/$NGINX_APP_SITE
	sudo ln $NGINX_CONFIG_ROOT/sites-{available,enabled}/$NGINX_MAINTENANCE_SITE
	sudo service nginx reload
}

function disable_maintenance {
	sudo rm -I $NGINX_CONFIG_ROOT/sites-enabled/$NGINX_MAINTENANCE_SITE
	sudo ln $NGINX_CONFIG_ROOT/sites-{available,enabled}/$NGINX_APP_SITE
	sudo service nginx reload
}

function update_backend {
	# Update application data
	source $VIRTUALENV_PATH/bin/activate
	pip install --upgrade --use-mirrors -r requirements.txt
	python manage.py migrate
	python manage.py compilemessages
	# Collect all staticfiles from dist/ and python packages to static/
	python manage.py collectstatic --noinput --clear
	deactivate
}

function check_build {
	if git rev-parse $1-build > /dev/null 2>&1
	then
		return 0
	else
		return 1
	fi
}

cd $APP_PATH

if $ENABLE_MAINTENANCE
then
	# Maintenance mode
	echo "Enabling maintenance mode"
	enable_maintenance
fi

# Fetching tags
git fetch --tags
# Server has git < 1.9, git fetch --tags doesn't retrieve commits...
git fetch

if check_build $1
then
	echo "Cleaning up"
	# Delete old branch if exists
	git checkout prod
	git branch -D $1
	# Removes dist/ folder to avoid conflicts
#	rm -rf ./dist/

	echo "Checking out tag $1-build"
	# Checkout the tag
	git checkout $1-build
	# Create a branch with the same name - required to have version data in footer
	git checkout -b $1

	echo "Updating app"
	update_backend

	echo "Restarting app"
	# Restart zds
	sudo supervisorctl restart zds
else
	echo "Build tag doesn't exist. Check travis build status maybe ?"
fi

if $ENABLE_MAINTENANCE
then
	# Exit maintenance mode
	echo "Disabling maintenance mode"
	disable_maintenance
fi

# Display current branch and commit
git status
echo "Deployed commit: `git rev-parse HEAD`"
