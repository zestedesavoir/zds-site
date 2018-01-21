#!/usr/bin/env bash

set -e

# Configure font folder
FONT_DIR="${HOME}/.local/share/fonts"
UPDATE_CACHE=false

mkdir -p ${FONT_DIR}
cd ${FONT_DIR}

function Download_Font {
    if [ $# -eq 1 ]
    then
        if [ ! -d "${1}" ]
        then
            UPDATE_CACHE=true
            mkdir ${1}
            cd ${1}

            wget -qO "${1}.zip" https://www.fontsquirrel.com/fonts/download/${1}
            unzip ${1}.zip
            rm -rf ${1}.zip

            cd ..

        else
            echo "Using cached font ${1}"
        fi
    fi
}

# Download Merriweather font

Download_Font merriweather

# Download Source Sans Pro

Download_Font source-sans-pro

# Download Source Code Pro

Download_Font source-code-pro

# Update cache
if [ $UPDATE_CACHE = true ]
then
    fc-cache -frv
else
    echo "Cache no need to be updated"
fi
