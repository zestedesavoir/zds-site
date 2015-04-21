========================
Installation du frontend
========================

Vous voulez nous aider au développement du frontend ? Installez Node.js et npm grâce aux instructions qui suivent !

Installation de Node.js et npm
==============================

Windows
-------

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

    sudo apt-get install nodejs

Mais il est possible d'avoir une version un peu plus récente avec :

.. sourcecode:: bash

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install nodejs

Certaines dépendances utilisent ``node`` au lieu de ``nodejs``, pour y remédier :

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

    sudo curl -sL https://rpm.nodesource.com/setup | bash -
    sudo yum install -y nodejs

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

Installation des dépendances npm
--------------------------------

L'installation de Gulp, ainsi que des différentes dépendances et bibliothèques, se fait via npm dans le répertoire du projet :

.. sourcecode:: bash

    npm install

Utilisation des outils
======================

Vous avez installé les outils ? Voilà comment on s'en sert dans notre projet !

Présentation de Gulp
--------------------

Gulp est un outil permettant d'automatiser les tâches liées au front. Dans notre cas, il permet de :

- Vérifier la syntaxe Javascript
- Minimiser les fichiers Javascript et les rassembler en un fichier
- Compiler les fichiers SCSS pour les transformer CSS
- Compresser les images et créer un sprite

.. note::

    Vous voulez en savoir plus ?
    Venez `ici <../front-end/design.html>`_ ! ;)

Utilisation de Gulp
-------------------

Gulp se lance avec ``npm run gulp -- [tâche]`` où ``[tâche]`` est la tâche à lancer. Les différentes tâches sont :

 - ``clean`` : Nettoie le dossier ``dist/``
 - ``build`` : Compile tout (SCSS, JS et images)
 - ``test`` : Lance les tests (grâce à JSHint)
 - ``watch`` : Compile les différents fichiers dès qu'ils sont modifiés (utile pour le développement ; ``Ctrl+C`` pour arrêter)

Si vos modifications n'apparaissent pas dans votre navigateur et que ce n'est pas dû à Gulp, pensez à vider le cache de votre navigateur !

-----

Pour information, la commande ``npm run`` est un raccourci de la commande ``npm run-script``, donc les deux commandes sont identiques !

Si vous voulez utiliser directement la commande ``gulp [tâche]`` au lieu de ``npm run gulp -- [tâche]``, il vous faut lancer cette commande avec les droits administrateurs :

.. sourcecode:: bash

    sudo npm install -g gulp

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