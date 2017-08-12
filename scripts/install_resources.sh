#!/bin/bash

if [[ -f "$HOME/.fonts/truetype/SourceCodePro/SourceCodePro-Regular.ttf" ]]; then
  echo "Using cached fonts"
else
  echo "Installing fonts"
  rm -rf $HOME/.fonts
  mkdir -p $HOME/.fonts/truetype
  cp -r export-assets/fonts/* $HOME/.fonts/truetype
  chmod a+r -R $HOME/.fonts/truetype/*
  echo "Installation complete !"
fi
# always refresh font cache because $HOME/.fonts has been added either here or via the cache
fc-cache -f -v

if [[ -f "$HOME/bin/pandoc" && -f "$HOME/.pandoc/templates/default.epub" ]]; then
  echo "Using cached pandoc"
else
  echo "Installing pandoc"
  rm -rf $HOME/.cabal $HOME/.pandoc
  mkdir -p $HOME/.cabal/bin
  mkdir -p $HOME/.pandoc
  unzip -u export-assets/pandoc/pandoc.zip -d $HOME/.cabal/bin
  mkdir -p $HOME/.pandoc/templates
  cp export-assets/pandoc/default.* $HOME/.pandoc/templates
  ln -sf $HOME/.cabal/bin/pandoc $HOME/bin/
  echo "Installation complete !"
fi
touch $HOME/.pandoc/epub.css
touch $HOME/.pandoc/templates/epub.css
chmod u+x,g+x,o+x $HOME/bin/*
$HOME/bin/pandoc --version
