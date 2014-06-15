# Sur Linux

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Les commandes suivantes sont génériques et indépendantes de la distribution que vous utilisez.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

Assurez vous que les dépendances suivantes soient résolues :
- git : `apt-get install git`
- python2.7
- python-dev : `apt-get install python-dev`
- easy_install : `apt-get install python-setuptools`
- pip : `easy_install pip`
- libxml2-dev : `apt-get install libxml2-dev`
- python-lxml : `apt-get install python-lxml`
- libxlst-dev (peut être appelée libxlst1-dev sur certains OS comme ubuntu
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse
- libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev : `apt-get install libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev`

## Front ou Back ?

Si vous ne comptez qu'au back-end du site, téléchargez le zip des ressources ici : http://zestedesavoir.com/static/pack.zip
Il faudra l'extraire dans le dossier `dist/` à la racine de votre projet.

Si vous comptez contribuer au front-end, rendez-vous sur [la documentation dédiée](gulp.md).

## Lancer ZdS

Une fois dans votre environnement python (`source ../bin/activate` si vous utilisez virtualenv, très fortement conseillé), lancez l'installation complète :

```console
pip install --upgrade -r requirements.txt
npm install
gulp build
python manage.py syncdb
python manage.py migrate
python manage.py runserver
```

## Aller plus loin

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX, Pandoc et les polices Microsoft. Ce qui revient à lancer les commmandes suivantes :

```console
apt-get install --reinstall ttf-mscorefonts-installer
apt-get install texlive
apt-get install texlive-xetex
apt-get install texlive-lang-french
apt-get install texlive-latex-extra
apt-get install haskell-platform
apt-get install cabal update
apt-get install cabal install pandoc
```