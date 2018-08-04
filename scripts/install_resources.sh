#!/bin/bash


EXTRA_PACKAGES="adjustbox blindtext capt-of catoptions cm-super collectbox framed fvextra glossaries ifplatform menukeys minted multirow ntheorem pagecolor relsize tabu varwidth xpatch xstring mfirstuc xfor datatool substr tracklang xsavebox media9 tcolorbox environ etoolbox trimspaces ifthen geometry xifthen ifmtarg fontspec luacode ctablestack"
EXTRA_PACKAGES_CACHE="$HOME/.texlive/extra_packages_cache.txt"

function install_texlive() {
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

  # save list of extra packages
  echo $EXTRA_PACKAGES > $EXTRA_PACKAGES_CACHE

  echo "Installation complete !"
}

if [[ -f $HOME/.texlive/bin/x86_64-linux/tlmgr ]]; then
  if [[ -f $EXTRA_PACKAGES_CACHE ]]; then
      if [[ $(cat $EXTRA_PACKAGES_CACHE) != $EXTRA_PACKAGES ]]; then
        echo "! found change in extra packages"
        install_texlive
      else
        echo "! no change detected: using cached texlive"
      fi
  else
    echo "! extra packages cache not found in $EXTRA_PACKAGES_CACHE"
    install_texlive
  fi
else
  echo "! previous installation not found"
  install_texlive
fi

# Symlink the binaries to ~/bin
for i in $HOME/.texlive/bin/x86_64-linux/*; do
  ln -sf $i $HOME/bin/
done
# install latex-template
# always refresh font cache because $HOME/.fonts has been added either here or via the cache
fc-cache -f -v
mkdir -p "$HOME/texmf/tex/latex/utf8.lua"
cd "$HOME/texmf/tex/latex/" && wget https://github.com/zestedesavoir/latex-template/archive/master.zip -O zmd.zip && unzip zmd
wget https://raw.githubusercontent.com/Stepets/utf8.lua/e698ef9621d95263838d33de5200cc855fc3f688/utf8.lua -O utf8.lua/utf8.lua
mv latex-template-master/*.cls ./ && mv latex-template-master/*.lua ./
cd "$HOME" && texhash
ls -l "$HOME/texmf/tex/latex/"
echo "Installation complete !"
