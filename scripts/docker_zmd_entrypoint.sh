#!/bin/sh -e
cd ./node_modules/zmarkdown

npm run server
pm2 monit
