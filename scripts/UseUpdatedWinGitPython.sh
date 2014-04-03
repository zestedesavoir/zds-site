#! /bin/sh

mkdir temp
cd temp

git clone https://github.com/bu-ist/GitPython.git

cd GitPython

git checkout 2fc864356ef1c4a9112dcefbae02a606df59840c

git apply ../../patchs/GitPython/add-commit-by-username.patch

python setup.py install

cd ..
rm -rf GitPython

cd ..
rm -rf temp