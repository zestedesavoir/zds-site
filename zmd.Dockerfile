FROM node:14-slim

COPY zmd/package.json ./package.json

RUN npm -g install pm2

RUN npm install --production

