#!/bin/bash
#
# Zeste de Savoir deployment script
#
# Deploys specified version of Zeste de Savoir
#
# Usage:
# - This script must be run by zds user
# - This script has exactly 1 parameter: the tag name to deploy

# Utility function to show what command is running
function exe {
	echo -e "+ \e[1m$@\e[0m" # show command (in bold)
	"$@" # and exe the command
}

# Defaults:
_D_ZDS_USER="zds"
_D_VIRTUALENV_PATH=/opt/zdsenv
_D_APP_PATH=/opt/zdsenv/ZesteDeSavoir
_D_NGINX_CONFIG_ROOT=/etc/nginx
_D_NGINX_MAINTENANCE_SITE=zds-maintenance
_D_NGINX_APP_SITE=zestedesavoir
_D_ENABLE_MAINTENANCE=true
_D_MANUAL_BUILD_FRONT=false

# Setting variables using env & defaults
: ${ZDS_USER:=$_D_ZDS_USER}
: ${VIRTUALENV_PATH:=$_D_VIRTUALENV_PATH}
: ${APP_PATH:=$_D_APP_PATH}
: ${NGINX_CONFIG_ROOT:=$_D_NGINX_CONFIG_ROOT}
: ${NGINX_MAINTENANCE_SITE:=$_D_NGINX_MAINTENANCE_SITE}
: ${NGINX_APP_SITE:=$_D_NGINX_APP_SITE}
: ${ENABLE_MAINTENANCE:=$_D_ENABLE_MAINTENANCE}
: ${MANUAL_BUILD_FRONT:=$_D_MANUAL_BUILD_FRONT}

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

# Diaplay config
echo "Here is the config:"
for varname in ZDS_USER VIRTUALENV_PATH APP_PATH NGINX_CONFIG_ROOT NGINX_MAINTENANCE_SITE NGINX_APP_SITE ENABLE_MAINTENANCE MANUAL_BUILD_FRONT
do
	default_varname=_D_$varname
	if [[ x${!default_varname} == x${!varname} ]]
	then
		echo " - $varname = ${!varname}"
	else
		echo -e " - $varname = \e[0;32m${!varname}\e[0m (default: ${!default_varname})"
	fi
done

read -p "Is this OK ? [y/N] " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
	echo "You can change these by setting environment variables."
	exit 1
fi

function enable_maintenance {
	exe sudo rm -I $NGINX_CONFIG_ROOT/sites-enabled/$NGINX_APP_SITE
	exe sudo ln $NGINX_CONFIG_ROOT/sites-{available,enabled}/$NGINX_MAINTENANCE_SITE
	exe sudo service nginx reload
}

function disable_maintenance {
	exe sudo rm -I $NGINX_CONFIG_ROOT/sites-enabled/$NGINX_MAINTENANCE_SITE
	exe sudo ln $NGINX_CONFIG_ROOT/sites-{available,enabled}/$NGINX_APP_SITE
	exe sudo service nginx reload
}

function clean_workspace {
	echo "Cleaning up"

	# Removes dist/ folder to avoid conflicts
	exe rm -rf ./dist/

	# Resetting HEAD
	exe git reset --hard

	# Delete old branch if exists and not on remote
	exe git checkout prod
	exe git branch -D $1
}

function update_backend {
	# Update application data
	exe source $VIRTUALENV_PATH/bin/activate
	exe pip install --upgrade --use-mirrors -r requirements.txt
	exe python manage.py migrate
	exe python manage.py compilemessages
	# Collect all staticfiles from dist/ and python packages to static/
	exe python manage.py collectstatic --noinput --clear
	exe deactivate
}

function update_frontend {
	if npm -v > /dev/null 2>&1
	then
		exe npm install
		exe npm run clean
		exe npm run build
	else
		echo -e "\e[31m npm not found, can't build front \e[0m"
	fi
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
exe git fetch --tags
# Server has git < 1.9, git fetch --tags doesn't retrieve commits...
exe git fetch

if $MANUAL_BUILD_FRONT
then
	clean_workspace $1

	echo "Checking out $1"
	exe git checkout $1

	echo "Updating app"
	update_frontend
	update_backend

	echo "Restarting app"
	# Restart zds
	exe sudo supervisorctl restart zds
else
	if check_build $1
	then
		clean_workspace $1

		echo "Checking out tag $1-build"
		# Checkout the tag
		exe git checkout $1-build
		# Create a branch with the same name - required to have version data in footer
		exe git checkout -b $1

		echo "Updating app"
		update_backend

		echo "Restarting app"
		# Restart zds
		exe sudo supervisorctl restart zds
	else
		echo "Build tag doesn't exist. Check travis build status maybe ?"
	fi
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
