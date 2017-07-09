#!/bin/bash
#
# Pushes front files to a new tag on GitHub

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <tag to build>" >&2
	exit 1
fi

# Adding GitHub OAuth token to login
git config --global user.name "ZDS-Bot"
git config --global user.email "zestedesavoir@gmail.com"
git config --global push.default simple

echo "Pushing front to GitHub"

# Detaching from head
git checkout --detach

# Adding dist/ and commiting
git add --force dist/
git commit -m "Automatic front build"

# Creating tag and pushing
TAG_NAME=$1-build
git tag -a $TAG_NAME -m "$1 with built front files"
git push https://${GITHUB_TOKEN}@github.com/zestedesavoir/zds-site.git $TAG_NAME

if [ $? -eq 0 ]
then
  echo "Front pushed to tag $TAG_NAME !"
else
  echo "Pushing to GitHub failed! Check the logs."
fi
