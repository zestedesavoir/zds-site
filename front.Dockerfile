FROM node:14-slim

ENV NODE_ENV=development

WORKDIR /src

COPY package.json ./package.json
COPY Gulpfile.js ./Gulpfile.js

RUN apt-get update
RUN apt-get install -y dh-autoreconf

RUN yarn install

VOLUME ["/src/assets"]
