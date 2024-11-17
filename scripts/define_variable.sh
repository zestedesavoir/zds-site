#!/bin/bash

if [[ $ZDS_VENV == "" ]]; then
    ZDS_VENV="zdsenv"
fi

if [[ $ZDS_VENV_VERSION == "" ]]; then
    ZDS_VENV_VERSION="20.24.5"
fi

if [[ $ZDS_PIP_VERSION == "" ]]; then
    ZDS_PIP_VERSION="24.3.1" # needs to be also updated in .github/workflows/ci.yml
fi

ZDS_NODE_VERSION=$(head -n 1 $ZDSSITE_DIR/.nvmrc)

if [[ $ZDS_NVM_VERSION == "" ]]; then
    ZDS_NVM_VERSION="0.39.5"
fi

if [[ $ZDS_TYPESENSE_VERSION == "" ]]; then
    ZDS_TYPESENSE_VERSION="27.0" # needs to be also updated in .github/workflows/ci.yml
fi

if [[ $ZDS_TYPESENSE_API_KEY == "" ]]; then
    ZDS_TYPESENSE_API_KEY="xyz"
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
