#! /bin/sh

mkdir temp
cd temp

# clone repository
git clone https://github.com/bu-ist/GitPython.git

cd GitPython

# checkout the correct commit
git checkout 2fc864356ef1c4a9112dcefbae02a606df59840c

# apply patch for supporting commit by user
git apply ../../patchs/GitPython/add-commit-by-username.patch

# install
python setup.py install --user

# cleanning
cd ..
rm -rf GitPython

cd ..
rm -rf temp


