#! /bin/bash
if [ -f server/selenium-server-standalone-2.53.1.jar ]
then
  echo 'selenium-server-standalone-2.53.1.jar already exists';
else
  if [ ! -d server ]
  then
    mkdir server;
  fi;
  cd server;
  wget http://selenium-release.storage.googleapis.com/2.53/selenium-server-standalone-2.53.1.jar;
  echo 'Please install geckodriver from https://github.com/mozilla/geckodriver/releases/';
fi
