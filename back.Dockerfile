FROM python:3.9

ENV PYTHONUNBUFFERED 1

# -----
# LATEX
# -----

# Install packages
RUN apt-get update
RUN apt-get install -y texlive texlive-luatex texlive-lang-french texlive-latex-extra texlive-fonts-extra xzdec librsvg2-bin imagemagick

# Init tree
RUN mkdir /root/texmf
RUN tlmgr init-usertree

# Install packages
RUN tlmgr option repository "$(echo http://ftp.math.utah.edu/pub/tex/historic/systems/texlive/`echo -n $(tlmgr --version) | tail -c 4`/tlnet-final)"
RUN updmap-user
RUN tlmgr update --list
RUN tlmgr install adjustbox
RUN tlmgr install blindtext
RUN tlmgr install capt-of
RUN tlmgr install catoptions
RUN tlmgr install chemgreek
#RUN tlmgr install cm-super
RUN tlmgr install collectbox
RUN tlmgr install ctablestack
RUN tlmgr install datatool
RUN tlmgr install environ
RUN tlmgr install etoolbox
RUN tlmgr install fontspec
RUN tlmgr install framed
RUN tlmgr install fvextra
RUN tlmgr install geometry
RUN tlmgr install ifmtarg
RUN tlmgr install ifplatform
RUN tlmgr install luacode
RUN tlmgr install menukeys
RUN tlmgr install mfirstuc
RUN tlmgr install mhchem
RUN tlmgr install minted
RUN tlmgr install multirow
RUN tlmgr install ntheorem
RUN tlmgr install pagecolor
RUN tlmgr install relsize
RUN tlmgr install substr
RUN tlmgr install tcolorbox
RUN tlmgr install tracklang
RUN tlmgr install trimspaces
RUN tlmgr install varwidth
RUN tlmgr install xfor
RUN tlmgr install xifthen
RUN tlmgr install xpatch
RUN tlmgr install xstring


# Install Tabu
RUN mkdir -p /src/texmf/tex/latex/tabu/
RUN wget -q https://raw.githubusercontent.com/tabu-issues-for-future-maintainer/tabu/master/tabu.sty -O /src/texmf/tex/latex/tabu/tabu.sty

RUN mkdir -p /src/texmf/tex/generic

# Get template

RUN wget -q https://github.com/zestedesavoir/latex-template/archive/master.tar.gz -O template.tar.gz
RUN tar -xf template.tar.gz
RUN cp -rp latex-template-master/* /root/texmf/tex/generic/
RUN rm -rf latex-template-master template.tar.gz

RUN texhash /root/texmf

# Get fonts

RUN mkdir -p /usr/local/share/fonts/opentype/source-code-pro
RUN mkdir -p /usr/local/share/fonts/opentype/source-sans-pro
RUN mkdir -p /usr/local/share/fonts/truetype/source-code-pro
RUN mkdir -p /usr/local/share/fonts/truetype/source-sans-pro


RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Black.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-Black.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-BlackIt.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-BlackIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Bold.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-Bold.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-BoldIt.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-BoldIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-ExtraLight.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-ExtraLight.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-ExtraLightIt.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-ExtraLightIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-It.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-It.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Light.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-Light.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-LightIt.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-LightIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Regular.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-Regular.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Semibold.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-Semibold.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-SemiboldIt.otf -O /usr/local/share/fonts/opentype/source-code-pro/SourceCodePro-SemiboldIt.otf

RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Black.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-Black.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-BlackIt.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-BlackIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Bold.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-Bold.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-BoldIt.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-BoldIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-ExtraLight.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-ExtraLight.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-ExtraLightIt.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-ExtraLightIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-It.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-It.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Light.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-Light.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-LightIt.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-LightIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Regular.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-Regular.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Semibold.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-Semibold.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-SemiboldIt.ttf -O /usr/local/share/fonts/truetype/source-code-pro/SourceCodePro-SemiboldIt.ttf

RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-Black.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-Black.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-BlackIt.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-BlackIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-Bold.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-Bold.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-BoldIt.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-BoldIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-ExtraLight.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-ExtraLight.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-ExtraLightIt.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-ExtraLightIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-It.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-It.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-Light.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-Light.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-LightIt.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-LightIt.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-Regular.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-Regular.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-Semibold.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-Semibold.otf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/OTF/SourceSans3-SemiboldIt.otf -O /usr/local/share/fonts/opentype/source-sans-pro/SourceSansPro-SemiboldIt.otf

RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Black.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-Black.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-BlackIt.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-BlackIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Bold.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-Bold.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-BoldIt.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-BoldIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-ExtraLight.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-ExtraLight.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-ExtraLightIt.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-ExtraLightIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-It.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-It.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Light.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-Light.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-LightIt.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-LightIt.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Regular.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-Regular.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Semibold.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-Semibold.ttf
RUN wget -q https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-SemiboldIt.ttf -O /usr/local/share/fonts/truetype/source-sans-pro/SourceSansPro-SemiboldIt.ttf

RUN fc-cache -f


# ------
# WEBAPP
# ------

ENV DOCKERIZE_VERSION v0.6.1
RUN wget -q https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

WORKDIR /src

COPY requirements.txt /src/requirements.txt
COPY requirements-dev.txt /src/requirements-dev.txt
COPY requirements-prod.txt /src/requirements-prod.txt

RUN pip3 install --upgrade pip
RUN pip3 -q install -r /src/requirements-dev.txt
RUN pip3 -q install -r /src/requirements-prod.txt



#COPY ./settings_docker.py /zds/zds/settings/docker.py
#COPY ./service/zds-watchdog.sh /zds/zds-watchdog.sh
#COPY ./service/zds-index.sh /zds/zds-index.sh
