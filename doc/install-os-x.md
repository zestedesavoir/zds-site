# Sur OS X

Pour installer une version locale de ZdS sur OS X, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Avant de vous lancez dans l'installation de l'environnement de zds, il faut quelques pré-requis :
* Installer [XCode](https://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12) pour pouvoir exécuter des commandes (g)cc.
* Installer [MacPorts](http://www.macports.org/) pour récupérer certains paquets utiles pour l'installation des dépendances de ce projet.
* Installer python 2.7
* Installer pip
* Installer git

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds.

## Installation de virtualenv

```console
pip install virtualenv
pip install virtualenvwrapper
mkdir ~/.virtualenvs
echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile && export WORKON_HOME=$HOME/.virtualenvs
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile && source /usr/local/bin/virtualenvwrapper.sh
```

## Création de votre environnement

```console
mkvirtualenv zdsenv
```

## Récupération de la librairie lxml pour python 2.7 via MacPorts

```console
sudo port install py27-lxml
```

## Ajout de flags pour compiler avec gcc plutôt que clang lors de l'installation de lxml

```console
export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments
```

## Front ou Back ?

Si vous ne comptez qu'au back-end du site, téléchargez le zip des ressources ici : http://zestedesavoir.com/static/pack.zip
Il faudra l'extraire dans le dossier `dist/` à la racine de votre projet.

Si vous comptez contribuer au front-end, rendez-vous sur [la documentation dédiée](gulp.md).

## Installation de toutes les dépendances

```console
pip install --upgrade -r requirements.txt
npm install
gulp build
```

Pour relancer votre environnement : `source ~/.virtualenvs/zdsenv/bin/activate`
Pour sortir de votre environnement : `deactive`

## Aller plus loin

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez [BasicTex](http://www.tug.org/mactex/morepackages.html)
- Téléchargez et installez [Pandoc](https://github.com/jgm/pandoc/releases)