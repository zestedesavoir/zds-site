# Installation du frontend

Vous voulez nous aider au développement du frontend ? Installez Node.JS et npm grâce aux instructions qui suivent !

## Installation de Node.js et npm

### Windows

Node.js propose un installeur (*.msi*) pour Windows, disponible à [cette adresse](http://nodejs.org/download/). Choisissez *Windows Installer*, avec l'architecture adéquate, et installez Node.js en ouvrant le fichier téléchargé.

### Mac OS X

Node.js propose un installeur (*.pkg*) pour Mac OS X, disponible à [cette adresse](http://nodejs.org/download/). Choisissez *Mac OS X Installer*, et installez Node.js en ouvrant le fichier téléchargé.

### Linux

#### Ubuntu

L'installation peut se faire simplement via `apt-get` :

````shell
sudo apt-get install nodejs
````

Mais il est possible d'avoir une version un peu plus récente avec :

````shell
sudo add-apt-repository ppa:chris-lea/node.js
sudo apt-get update
sudo apt-get install nodejs
````

Certaines dépendances utilisent `node` au lieu de `nodejs`, pour y remédier :

````shell
sudo ln -s /usr/bin/nodejs /usr/bin/node
````

#### Debian

Une version récente de Node.js se trouve dans les dépôts *wheezy-backport*, *jessie* et *sid*. Sur ces versions de Debian, l'installation peut se faire de cette manière :

````shell
sudo apt-get install nodejs
````

#### Fedora / CentOS / RHEL

Il vous faut tout simplement faire :

````shell
sudo curl -sL https://rpm.nodesource.com/setup | bash -
sudo yum install -y nodejs
````

#### Arch Linux

Il faut simplement lancer cette commande : 

````shell
pacman -S nodejs
````

### FreeBSD / OpenBSD

Une installation via `pkg` devrait suffire :

````shell
pkg install node
````

-----

*Les instructions pour installer Node.js sur les distributions CentOS, RHEL, FreeBSD et OpenBSD sont issues du lien juste en dessous et n'ont pas été testées.*

Les **instructions détaillées** pour toutes les distributions se trouvent dans la [**documentation officielle** (en anglais)](https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager).

Pour vérifier que Node.js et npm sont installés (et que vous avez les bonnes versions) :

````shell
node -v
v0.10.26
npm -v
2.1.7
````

**Vous devez avoir une version de Node.js > 0.10.x et de npm > 2.x.x.** Si votre version de npm est 1.x.x, vous devez le mettre à jour (voir juste en dessous).

## Mise à jour de Node.js et npm

Pour npm, il suffit de le mettre à jour avec cette commande :

````shell
sudo npm install -g npm
````

Pour ce qui est de Node.js, une mise à jour via le gestionnaire de paquets devrait fonctionner.

## Installation des dépendances npm

L'installation de Gulp, ainsi que des différentes dépendances et bibliothèques, se fait via npm dans le répertoire du projet :

````shell
npm install
````

# Utilisation des outils

Vous avez installé les outils ? Voilà comment on s'en sert dans notre projet !

## Présentation de Gulp

Gulp est un outil permettant d'automatiser les tâches liées au front. Dans notre cas, il permet de :

- Vérifier la syntaxe Javascript
- Minimiser les fichiers Javascript et les rassembler en un fichier
- Compiler les fichiers SCSS pour les transformer CSS
- Compresser les images et créer un sprite

Il y a, à la racine du projet, un dossier `assets/` (contenant les sources JS et SCSS non minimisées, ainsi que les images) qui ressemble à ça :

````shell
assets/
├── images/
│   ├── favicon.ico
│   ├── favicon.png
│   ├── logo@2x.png
│   ├── logo.png
│   ...
├── js/
│   ├── accessibility-links.js
│   ├── data-click.js
│   ...
├── scss/
│   ├── main.scss
│   ├── _mobile.scss
│   ├── _mobile-tablet.scss
│   ...
└── smileys/
    ├── ange.png
    ├── angry.gif
    ...
````

Après le passage de Gulp, toujours à la racine du projet, est créé un dossier `dist/` (contenant des fichiers optimisés pour la production) qui est similaire à ça :

````shell
dist/
├── css
│   ├── main.css # Tout le CSS compilé...
│   └── main.min.css # ...et minimisé
├── images # Toutes les images optimisées
│   ├── favicon.ico
│   ├── favicon.png
│   ├── logo@2x.png
│   ...
├── js
│   ├── all.min.js # Tout le JS minimisé
│   ├── main.js # Tout le JS customisé...
│   ├── main.min.js # ...et minimisé
│   ├── vendors # Toutes les bibliothèques non-minimisées
│   │   ├── jquery.js
│   │   └── modernizr.js
│   ├── vendors.js # Toutes les bibliothèques rassemblées...
│   └── vendors.min.js # ...et minimisées
└── smileys
    ├── ange.png
    ├── angry.gif
    ...
````

## Utilisation de Gulp

Gulp se lance avec `npm run gulp -- [tâche]` où `[tâche]` est la tâche à lancer. Les différentes tâches sont :

 - `clean`: Nettoie le dossier `dist/`
 - `build`: Compile tout (SCSS, JS et images)
 - `test`: Lance les tests (grâce à JSHint)
 - `watch`: Compile les différents fichiers dès qu'ils sont modifiés (utile pour le développement ; `Ctrl+C` pour arrêter)

Si vos modifications n'apparaissent pas dans votre navigateur et que ce n'est pas dû à Gulp, pensez à vider le cache de votre navigateur !

-----

Pour information, la commande `npm run` est un raccourci de la commande `npm run-script`, donc les deux commandes sont identiques !

Si vous voulez utiliser directement la commande `gulp [tâche]` au lieu de `npm run gulp -- [tâche]`, il vous faut lancer cette commande avec les droits administrateurs :

````shell
sudo npm install -g gulp
````

# Nettoyage des outils

## Désinstaller les dépendances

Il vous suffit pour cela de lancer la commande :

````shell
npm uninstall
````

Si ça ne fonctionne pas, vous pouvez le faire manuellement grâce à `rm -rI node_modules/`.

## Désinstaller les dépendances inutilisées

Il y a une commande toute faite pour ça :

````shell
npm prune
````