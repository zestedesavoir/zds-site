#!/bin/bash

if [[ $ZDS_VENV == "" ]]; then
    ZDS_VENV="zdsenv"
fi

if [[ $ZDS_VENV_VERSION == "" ]]; then
    ZDS_VENV_VERSION="20.24.5"
fi

ZDS_NODE_VERSION=$(cat $ZDSSITE_DIR/.nvmrc)

if [[ $ZDS_NVM_VERSION == "" ]]; then
    ZDS_NVM_VERSION="0.39.5"
fi

if [[ $ZDS_ELASTIC_VERSION == "" ]]; then
    ZDS_ELASTIC_VERSION="5.5.2"
fi

if [[ $ZDS_LATEX_REPO == "" ]]; then
    ZDS_LATEX_REPO="https://github.com/zestedesavoir/latex-template.git"
fi

if [[ $ZDS_JDK_VERSION == "" ]]; then
    ZDS_JDK_VERSION="11.0.20.1"
    # shellcheck disable=SC2034
    ZDS_JDK_REV="1"
fi

if [[ $ZMD_URL == "" ]]; then
    ZMD_URL="http://localhost:27272"
fi
