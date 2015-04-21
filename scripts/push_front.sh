#!/bin/bash
#
# Pushes front files to a new tag on GitHub

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <tag to build>" >&2
	exit 1
fi

echo "Pushing front to GitHub"

# Detaching from head
git checkout --detach

# Adding dist/ and commiting
git add --force dist/
git commit -m "Automatic front build"

# Creating tag and pushing
TAG_NAME=$1-build
git tag -a $TAG_NAME -m "$1 with built front files"
git push origin $TAG_NAME

echo "Front pushed to tag $TAG_NAME !"
