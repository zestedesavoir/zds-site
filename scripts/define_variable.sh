#!/bin/bash

if [[ $ZDS_VENV == "" ]]; then
    ZDS_VENV="zdsenv"
fi

if [[ $ZDS_NODE_VERSION == "" ]]; then
    ZDS_NODE_VERSION="10.8.0"
fi

if [[ $ZDS_NVM_VERSION == "" ]]; then
    ZDS_NVM_VERSION="0.33.11"
fi

if [[ $ZDS_ELASTIC_VERSION == "" ]]; then
    ZDS_ELASTIC_VERSION="5.5.2"
fi

if [[ $ZDS_LATEX_REPO == "" ]]; then
    ZDS_LATEX_REPO="https://github.com/zestedesavoir/latex-template.git"
fi
