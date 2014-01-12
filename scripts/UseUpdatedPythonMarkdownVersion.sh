#! /usr/bin/sh

mkdir temp
cd temp

# clone repository
git clone git://github.com/waylan/Python-Markdown.git python-markdown
cd python-markdown

# checkout the correct commit
git checkout 73fdecaf2cf00d85b7c933f5b8d186d74a80ff2a

# install
python setup.py install --user

# cleanning
cd ..
rm -rf python-markdown

cd ..
rm -rf temp


