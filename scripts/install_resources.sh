#!/bin/bash

EXTRA_PACKAGES="adjustbox blindtext capt-of catoptions cm-super collectbox framed fvextra glossaries ifplatform menukeys minted multirow ntheorem pagecolor relsize tabu varwidth xpatch xstring mfirstuc xfor datatool substr tracklang"

if [[ -f $HOME/.texlive/bin/x86_64-linux/tlmgr ]]; then
  echo "Using cached texlive install"
else
  # Force cache upload after successful build
  touch $HOME/.cache_updated
  echo "Installing texlive to \$HOME/.texlive"
  rm -rf $HOME/.texlive
  TEXLIVE_PROFILE=${BASH_SOURCE[0]/%install_resources.sh/texlive.profile}

  # Create install dir
  mkdir -p $HOME/.texlive/
  cp $TEXLIVE_PROFILE $HOME/.texlive/
  cd $HOME/.texlive/

  # Fix paths in profile (needs absolute paths)
  sed -i 's@\$HOME@'"$HOME"'@' texlive.profile

  # Download and run installer
  wget -O install-tl.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
  tar xzf install-tl.tar.gz

  ./install-tl*/install-tl -profile texlive.profile

  # Install extra latex packages
  $HOME/.texlive/bin/x86_64-linux/tlmgr install $EXTRA_PACKAGES
  $HOME/.texlive/bin/x86_64-linux/tlmgr update --self

  echo "Installation complete !"
fi
