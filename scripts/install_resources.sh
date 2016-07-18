#!/bin/bash
export RESOURCES_URL="http://www.googledrive.com/host/0BzabS14KitJgfmV2ekdWSktmVEpieU93TG11RFNkWlZqS0JwZk93ZGhMR1lCWVg5NzFVc00"

if [[ -f "$HOME/.fonts/truetype/Andale-Mono.ttf" ]]; then
  echo "Using cached fonts"
else
  # force cache upload after successful build
  touch $HOME/.cache_updated
  echo "Installing fonts"
  rm -rf $HOME/.fonts
  mkdir -p $HOME/.fonts/truetype
  wget -P $HOME/.fonts/truetype $RESOURCES_URL/Andale-Mono.ttf
  wget -P $HOME/.fonts/truetype $RESOURCES_URL/Merriweather.zip
  unzip -u $HOME/.fonts/truetype/Merriweather.zip -d $HOME/.fonts/truetype/Merriweather/
  chmod a+r $HOME/.fonts/truetype/Merriweather/*.ttf
  chmod a+r $HOME/.fonts/truetype/Andale-Mono.ttf
  echo "Installation complete !"
fi
# always refresh font cache because $HOME/.fonts has been added either here or via the cache
fc-cache -f -v

if [[ -f "$HOME/bin/pandoc" && -f "$HOME/.pandoc/templates/default.epub" ]]; then
  echo "Using cached pandoc"
else
  # force cache upload after successful build
  touch $HOME/.cache_updated
  echo "Installing pandoc"
  rm -rf $HOME/.cabal $HOME/.pandoc
  mkdir -p $HOME/.cabal/bin
  mkdir -p $HOME/.pandoc
  wget -P $HOME/.cabal/bin $RESOURCES_URL/pandoc
  wget -P $HOME/.pandoc/templates $RESOURCES_URL/default.epub
  wget -P $HOME/.pandoc/templates $RESOURCES_URL/default.html
  ln -sf $HOME/.cabal/bin/pandoc $HOME/bin/
  echo "Installation complete !"
fi
touch $HOME/.pandoc/epub.css
touch $HOME/.pandoc/templates/epub.css
chmod u+x,g+x,o+x $HOME/bin/*
$HOME/bin/pandoc --version
