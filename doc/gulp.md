# tl;dr — Installation rapide

Installez [node.js](http://nodejs.org), puis, dans le dossier du projet :

````shell
[sudo] npm install -g bower gulp # Installe gulp et bower, si ce n'est pas déjà fait
npm install # Installe les dépendances du projet
gulp build # Lance gulp
````

# Installer Gulp

## Prérequis

### [Node.js](http://nodejs.org)

Pour vérifier si vous avez node d'installé :

````shell
$ node -v
v0.10.26
$ npm -v
1.4.7
````

Vous devez avoir une version de node > 0.10.x, et de npm > 1.x.x

#### Windows

Node.js propose un installeur (*.msi*) pour Windows, disponible à [cette addresse](http://nodejs.org/download/). Choisissez *Windows Installer*, avec l'architecture adéquate, et installez Node en ouvrant le fichier téléchargé.

#### Mac OS X

Node.js propose un installer (*.pkg*) pour Mac OS X, disponible à [cette addresse](http://nodejs.org/download/). Choisissez *Mac OS X Installer*, et installez Node en ouvrant le fichier téléchargé.

#### Linux

##### Ubuntu

Une version récente de Node avec npm est disponible sur le PPA `chris-lea/node.js`

````shell
$ sudo add-apt-repository ppa:chris-lea/node.js
$ sudo apt-get update
$ sudo apt-get install python-software-properties python g++ make nodejs
````

##### Debian

Une version récente de Node se trouve dans les répos wheezy-backport, jessie, et sid. Sur ces versions de Debian, l'installation peut se faire de cette manière:

````shell
$ sudo apt-get install node
````

-----

Les instructions détaillées pour toutes les distributions se trouvent dans la [doc officielle (en anglais)](https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager)

### Gulp et Bower

L'installation de Gulp et Bower se fait via `npm`. Selon votre installation, elle devra se faire en administrateur ou non.

````shell
$ [sudo] npm install -g gulp bower
````

### Installer les dépendances npm du projet

Dans le répertoire du projet, lancez simplement `npm install`. Cela installera les dépendances des tâches Gulp, et les dépendances front via Bower (jQuery, Modernizr, ...)

# Utiliser Gulp

## Présentation

Gulp est un outil permettant d'automatiser les tâches liées au front.
Dans notre cas, il permet de :

- Vérifier la syntaxe Javascript (JSHint)
- Rassembler en un fichier et minimifier les fichiers Javascript
- Compiler les fichiers SCSS, pour les transformer CSS (via compass)
- Compresser les images

Il y a un dossier `assets/` à la racine, qui ressemble à ça :

````shell
assets/
├── bower_components
│   ├── jquery
│   └── modernizr
│   ...
├── images
│   ├── favicon.ico
│   ├── favicon.png
│   ├── logo@2x.png
│   ...
├── js
│   ├── accessibility-links.js
│   ├── data-click.js
│   ...
├── scss
│   ├── main.scss
│   ├── _mobile.scss
│   ├── _mobile-tablet.scss
│   ...
└── smileys
    ├── ange.png
    ├── angry.gif
    ...
````

Et le build gulp donne un dossier `dist/`, avec des fichiers optimisés pour la production, comme pour le développement

````shell
dist/
├── css
│   ├── main.css # CSS compilé
│   └── main.min.css # version minimifié
├── images # Les images ont été optimisées
│   ├── favicon.ico
│   ├── favicon.png
│   ├── logo@2x.png
│   ...
├── js
│   ├── all.min.js # Vendors + custom, minimifié 
│   ├── main.js # Tout le JS Custom
│   ├── main.min.js # Version minimifiée
│   ├── vendors # Les dépendances (non-minimifiées)
│   │   ├── jquery.js
│   │   └── modernizr.js
│   ├── vendors.js # Toutes les dépendances rassemblées 
│   └── vendors.min.js # Version minimifiée
└── smileys
    ├── ange.png
    ├── angry.gif
    ...
````

## Les différentes tâches

Gulp se lance avec `gulp [tache]`, où "*[tache]*" est la tâche à lancer.

 - `clean`: Nettoie le dossier `dist/`
 - `build`: Compile tout (CSS, JS, et Images)
 - `test`: Lance les tests (JSHint, ...)
 - `watch`: Compile les différents fichiers dès qu'ils sont modifiés (utile pour le développement; `Ctrl+C` pour arrêter)