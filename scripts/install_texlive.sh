#!/bin/bash
#
# Install texlive to $HOME/.texlive

TEXLIVE_PROFILE=${BASH_SOURCE[0]/%install_texlive.sh/texlive.profile}

# Creating install dir
mkdir -p ~/.texlive/
cp $TEXLIVE_PROFILE ~/.texlive/
cd ~/.texlive/

# Replace correct paths in profile (needs absolute paths)
sed -i 's@\$HOME@'"$HOME"'@' texlive.profile

# Download and run installer
wget -O ./install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
tar -zxf ./install-tl.tar.gz
./install-tl*/install-tl -profile texlive.profile

# Install extra latex packages
./bin/x86_64-linux/tlmgr install wallpaper titlesec

echo "Installation complete ! Don't forget to add ~/.texlive/bin/x86_64-linux to PATH"
