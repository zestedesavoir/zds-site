========================
Installation du frontend
========================

Vous voulez nous aider au développement du frontend ? Installez Node.js et npm grâce aux instructions qui suivent !


Installation de Node.js et npm
==============================

Windows
-------

.. Attention::

    Cette partie de la documentation n'est probablement pas à jour faute de contributeur utilisant Windows. Il se peut que l'installation fonctionne correctement, partiellement ou pas du tout. Bref, en cas de problème n'hésitez pas à venir demander de l'aide sur le `forum des Devs' de Zeste de Savoir <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ !

Node.js propose un installeur (*.msi*) pour Windows, disponible à `cette adresse <http://nodejs.org/download/>`_. Choisissez *Windows Installer*, avec l'architecture adéquate, et installez Node.js en ouvrant le fichier téléchargé.

Vérifiez de posséder la version 2.5.0 de npm (et non la version 1.4.X que peut installer l'installeur), pour connaitre votre version : ``npm -v``. Pour mettre à jour npm, vous avez `trois possibilités <https://github.com/npm/npm/wiki/Troubleshooting#upgrading-on-windows)>`_, l'une d'elle est de faire ``npm install npm`` dans le dossier ``C:\Program Files (x86)\nodejs``.

Veillez à respecter `ces conditions <https://github.com/TooTallNate/node-gyp#installation>`_, avant de faire  ``npm install`` (dans l'ordre d'installation) :

- `Visual C++ 2010 Express <http://go.microsoft.com/?linkid=9709949>`_.
- `Windows 7 64-bit SDK <http://www.microsoft.com/en-us/download/details.aspx?id=8279>`_, si vous êtes en 64bits.

  En cas de problème, avec l'installation du SDK, suivez `ces instructions <http://www.mathworks.com/matlabcentral/answers/95039#answer_104391>`_ :
   - Désinstallez : **Microsoft Visual C++ 2010 redistributable packages (x86 et x64)**, *dans le panneau de configuration*.
   - Relancez **Windows 7 64-bit SDK**, décochez "**Visual C++ Compilers**" et "**Microsoft Visual C++ 2010**".
   - Appliquez ce patch : `SDK 7.1 <http://www.microsoft.com/en-us/download/details.aspx?id=4422>`_.
   - Réinstallez (ils se sont peut-être déjà réinstallés tous seuls) `Microsoft Visual C++ 2010 redistributable x64 <http://www.microsoft.com/en-us/download/details.aspx?id=14632>`_ et `Microsoft Visual C++ 2010 redistributable x86 <http://www.microsoft.com/en-us/download/details.aspx?id=5555>`_.

- Vous devez posséder `Visual Studio Express 2013 pour Windows Desktop <https://app.vssps.visualstudio.com/profile/review?download=true&family=VisualStudioExpressDesktop>`_, la version 2012 ne suffit pas, forcez l'utilisation de vs 2013 comme ceci : ``npm install --msvs_version=2013``, il est même conseillé de faire ``npm config set msvs_version 2013``, pour les futurs installations/commandes.

Mac OS X
--------

Node.js propose un installeur (*.pkg*) pour Mac OS X, disponible à `cette adresse <http://nodejs.org/download/>`_. Choisissez *Mac OS X Installer*, et installez Node.js en ouvrant le fichier téléchargé.

Linux
-----

Ubuntu
~~~~~~

L'installation peut se faire simplement via ``apt-get`` :

.. sourcecode:: bash

    sudo apt-get install nodejs npm nodejs-legacy

Mais il est possible d'avoir une version un peu plus récente avec :

.. sourcecode:: bash

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install nodejs

Certaines dépendances utilisent ``node`` au lieu de ``nodejs``, pour y remédier (pas besoin sous Fedora !) :

.. sourcecode:: bash

    sudo ln -s /usr/bin/nodejs /usr/bin/node

Debian
~~~~~~

Une version récente de Node.js se trouve dans les dépôts *wheezy-backport*, *jessie* et *sid*. Sur ces versions de Debian, l'installation peut se faire de cette manière :

.. sourcecode:: bash

    sudo apt-get install nodejs

Fedora / CentOS / RHEL
~~~~~~~~~~~~~~~~~~~~~~

Il vous faut tout simplement faire :

.. sourcecode:: bash

    sudo dnf install nodejs

Arch Linux
~~~~~~~~~~

Il faut simplement lancer cette commande : 

.. sourcecode:: bash

    pacman -S nodejs

FreeBSD / OpenBSD
-----------------

Une installation via ``pkg`` devrait suffire :

.. sourcecode:: bash

    pkg install node

-----

*Les instructions pour installer Node.js sur les distributions CentOS, RHEL, FreeBSD et OpenBSD sont issues du lien juste en dessous et n'ont pas été testées.*

Les **instructions détaillées** pour toutes les distributions se trouvent dans la `documentation officielle (en anglais) <https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Pour vérifier que Node.js et npm sont installés (et que vous avez les bonnes versions) :

.. sourcecode:: bash

    node -v
    v0.10.26
    npm -v
    2.1.7

**Vous devez avoir une version de Node.js > 0.10.x et de npm > 2.x.x.** Si votre version de npm est 1.x.x, vous devez le mettre à jour (voir juste en dessous).

Mise à jour de Node.js et npm
-----------------------------

Pour npm, il suffit de le mettre à jour avec cette commande :

.. sourcecode:: bash

    sudo npm install -g npm

Pour ce qui est de Node.js, une mise à jour via le gestionnaire de paquets devrait fonctionner.

.. note::
   En cas de gros pépin avec l'installation de npm, il peut arriver que ce dernier soit complètement en vrac. Dans ce genre de situation, ce `lien StackOverflow <http://stackoverflow.com/questions/31025048/npm-doesnt-work-get-always-this-error-error-cannot-find-module-are-we-ther>`_ peut vous sauver ;) .


Installation des dépendances npm
--------------------------------

L'installation de Gulp, ainsi que des différentes dépendances et bibliothèques, se fait via npm dans le répertoire du projet :

.. sourcecode:: bash

    npm install # A faire dans le répertoire du clone de votre fork, installe Gulp et d'autres outils frontend - ne PAS être sudo


Utilisation des outils
======================

Vous avez installé les outils ? Voilà comment on s'en sert dans notre projet !

Présentation de Gulp
--------------------

Gulp est un outil permettant d'automatiser les tâches liées au *front-end*. Dans notre cas, il permet de :

- vérifier la syntaxe Javascript ;
- minimiser les fichiers Javascript et les rassembler en un fichier ;
- compiler les fichiers SCSS pour les transformer CSS ;
- compresser les images et créer un sprite.

Utilisation de Gulp
-------------------

Gulp se lance avec ``npm run gulp -- [tâche]`` où ``[tâche]`` est la tâche à lancer.

Générer les fichiers avec ``build``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Saisissez la commande suivante (elle vous permet de générer les fichiers Web du site pour vous permettre de consulter Zeste de Savoir sur votre navigateur, en local) :

.. sourcecode:: bash

    npm run gulp build # A faire dans le répertoire du clone de votre fork, crée le répertoire "dist" - Ne PAS être sudo, activation de l'environnement Python requise

``build`` permet de :

- minimiser les fichiers Javascript et les rassembler en un fichier ;
- compiler les fichiers SCSS pour les transformer CSS ;
- compresser les images et créer un sprite.

Les fichiers générés sont disponibles dans le dossier ``dist/`` (un aperçu est disponible
`ici <../front-end/arborescence-des-fichiers.html>`_).

.. note::
   C'est la tâche que vous utiliserez sûrement le plus souvent car vous devez la lancer à chaque modification
   de ``assets/`` !

Si vos modifications n'apparaissent pas dans votre navigateur et que ce n'est pas dû à Gulp, pensez à vider le
cache de votre navigateur !

Supprimer les fichiers générés avec ``clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``clean`` supprime les fichiers générés par ``build`` (il supprime simplement le dossier ``dist/``).

Vérifier le code avec ``test``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``test`` vérifie, par le biais de JSHint, la forme du code (indentation, doubles guillemets, etc). Si le code ne
respecte pas ces règles, le script va sortir une liste d'erreurs (*errors*) et/ou d'avertissements (*warnings*)
que vous devez corriger.

.. note::
   L'outil d'intégration continue que nous utilisons, Travis CI, fait cette vérification à la création de chaque
   *pull request* et sortira la liste des erreurs et des avertissements. Pour éviter d'attendre qu'il ait fini,
   il est plus pratique pour vous (et nous) que vous lanciez cette commande en amont avec ``npm run gulp -- test``
   (ou ``npm test``).

Coder plus simplement avec ``watch``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``watch`` surveille les fichiers SCSS et Javascript lance la tâche ``build`` dès qu'ils sont modifiés. C'est très
utile pour le développement car ça permet de ne pas avoir à relancer ``build`` manuellement. Pour arrêter cette
commande, il suffit de presser ``Ctrl+C``.

-----

.. seealso::

    Vous voulez en savoir plus ?
    Venez voir `la documentation consacrée au front-end <../front-end.html>`_ ! ;)

Quelques informations supplémentaires
-------------------------------------

La commande ``npm run`` est un raccourci de la commande ``npm run-script``, donc les deux commandes sont identiques !

Si vous voulez utiliser directement la commande ``gulp -- [tâche]`` au lieu de ``npm run gulp -- [tâche]``, vous pouvez
tout simplement créer un alias :

.. sourcecode:: bash

    alias gulp="npm run gulp"


Nettoyage des outils
====================

Désinstaller les dépendances
----------------------------

Il vous suffit pour cela de lancer la commande :

.. sourcecode:: bash

    npm uninstall

Si ça ne fonctionne pas, vous pouvez le faire manuellement grâce à ``rm -rI node_modules/``.

Désinstaller les dépendances inutilisées
----------------------------------------

Il y a une commande toute faite pour ça :

.. sourcecode:: bash

    npm prune
