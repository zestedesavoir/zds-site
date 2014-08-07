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
- libxslt-dev (peut être appelée libxslt1-dev sur certains OS comme ubuntu
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse
- libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev : `apt-get install libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev`

## Front ou Back ?

Si vous ne comptez qu'au back-end du site, téléchargez le zip des ressources ici : http://zestedesavoir.com/static/pack.zip
Il faudra l'extraire dans le dossier `dist/` à la racine de votre projet.

Si vous comptez contribuer au front-end, rendez-vous sur [la documentation dédiée](gulp.md).

## Installer et configurer `virtualenv`

(cette étape n'est pas obligatoire, mais fortement conseillée)

Si vous désirez employer un environement virtuel python de dévellopement, installez `virtualenv` et `virtualenvwrapper`. Dans cet environement, vous pourrez ensuite installer différents packages via `pip` sans qu'ils ne soient installés dans votre environement python principal. Cela permet, par exemple, de travailler avec différentes version de Django ou encore d'installer les dépendances sans vous inquiéter de créer des conflits dans d'autres projets.

L'installation ce fait grâce aux commandes suivantes :

```console
pip install virtualenv
pip install virtualenvwrapper
```

Exécutez ensuite les commandes suivantes, afin de configurer les deux outils :

```console
mkdir ~/.virtualenvs
echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc && export WORKON_HOME=$HOME/.virtualenvs
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc && source /usr/local/bin/virtualenvwrapper.sh
```

Créez ensuite votre environement virtuel grâce à 

```console
mkvirtualenv zdsenv
```

**À chaque fois** que vous souhaiter travailler dans votre environement (que ce soit pour installer des packages ou exécuter Django), employez la commande suivante :

```console
workon zdsenv
```

À noter que `workon` supporte l'auto-complétion. Pour ensuite le quitter, il suffira d'employer :

```console
deactivate
```

Une documentation plus complète de ces deux outils [est disponible ici](http://docs.python-guide.org/en/latest/dev/virtualenvs/).


## Lancer ZdS

Une fois dans votre environnement python (`workon zdsenv` si vous utilisez virtualenvwrapper), lancez l'installation complète :

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
