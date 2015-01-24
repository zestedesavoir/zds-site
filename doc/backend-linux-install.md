# Installation du backend sous Linux

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

Assurez vous que les dépendances suivantes soient résolues :
- git : `apt-get install git`
- python2.7
- python-dev : `apt-get install python-dev`
- easy_install : `apt-get install python-setuptools`
- pip : `easy_install pip`
- libxml2-dev : `apt-get install libxml2-dev`
- python-lxml : `apt-get install python-lxml`
- libxslt-dev (peut être appelée libxslt1-dev sur certaines distributions comme Ubuntu)
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse : `apt-get install python-sqlparse`
- libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev : `apt-get install libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev`

Ou, en une ligne,

```console
apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev
easy_install pip
```

## Installation et configuration de `virtualenv`

(cette étape n'est pas obligatoire, mais fortement conseillée)

```console
pip install virtualenv
virtualenv zdsenv --python=python2
```

**À chaque fois** que vous souhaitez travailler dans votre environement, activez le via la commande suivante :

```console
source zdsenv/bin/activate
```

Une documentation plus complète de cet outil [est disponible ici](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

## Installation des outils front-end

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur [la documentation dédiée](frontend-install.md).

## Lancer ZdS

Une fois dans votre environnement python (`source zdsenv/bin/activate` si `virtualenv`), lancez l'installation complète :

```console
pip install --upgrade -r requirements.txt
python manage.py syncdb
python manage.py migrate
python manage.py runserver
```

## Aller plus loin

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX, Pandoc et les polices Microsoft. Ce qui revient à lancer les commmandes suivantes :

```console
apt-get install --reinstall ttf-mscorefonts-installer
apt-get install texlive texlive-xetex texlive-lang-french texlive-latex-extra
apt-get install haskell-platform
cabal update
cabal install pandoc
```
