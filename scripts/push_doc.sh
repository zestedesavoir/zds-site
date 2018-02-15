#!/bin/bash
#
# Push documentation on the gh-pages branch

echo "Move the generated doc in a new branch"
touch doc/build/html/.nojekyll
echo "docs.zestedesavoir.com" > doc/build/html/CNAME
git add doc/build/html -f
git commit -m "Build documentation"
git subtree split --branch build_doc --prefix doc/build/html
echo "Push the documentation"
git push origin build_doc:gh-pages -f
