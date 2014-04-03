#! /bin/sh

mkdir temp
cd temp

# clone repository
git clone https://github.com/zeste-de-savoir/Python-ZMarkdown.git python-markdown
cd python-markdown

# checkout the correct commit
git checkout 2.4-zds.1 

# install
python setup.py install

# cleanning
cd ..
rm -rf python-markdown

cd ..
rm -rf temp


