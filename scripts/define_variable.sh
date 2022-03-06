#!/bin/bash

if [[ $ZDS_VENV == "" ]]; then
    ZDS_VENV="zdsenv"
fi

ZDS_NODE_VERSION=$(cat $ZDSSITE_DIR/.nvmrc)

if [[ $ZDS_NVM_VERSION == "" ]]; then
    ZDS_NVM_VERSION="0.33.11"
fi

if [[ $ZDS_ELASTIC_VERSION == "" ]]; then
    ZDS_ELASTIC_VERSION="5.5.2"
fi

if [[ $ZDS_LATEX_REPO == "" ]]; then
    ZDS_LATEX_REPO="https://github.com/zestedesavoir/latex-template.git"
fi

if [[ $ZDS_JDK_VERSION == "" ]]; then
    ZDS_JDK_VERSION="11.0.14.1"
    # shellcheck disable=SC2034
    ZDS_JDK_REV="1"
fi

if [[ $ZMD_URL == "" ]]; then
    ZMD_URL="http://localhost:27272"
fi

