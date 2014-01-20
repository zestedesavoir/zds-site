#! /bin/sh

mkdir temp
cd temp

# clone repository
git clone git://github.com/waylan/Python-Markdown.git python-markdown
cd python-markdown

# checkout the correct commit
git checkout 73fdecaf2cf00d85b7c933f5b8d186d74a80ff2a

# apply patch for supporting range line numbering
git apply ../../patchs/python-markdown/0001-Add-range-support-for-HL-in-codehilite.patch
git apply ../../patchs/python-markdown/0002-linenostart-support.patch

# install
python2 setup.py install --user

# cleanning
cd ..
rm -rf python-markdown

cd ..
rm -rf temp


