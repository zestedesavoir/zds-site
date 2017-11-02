==================================
Installation du backend sous Linux
==================================

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.

- Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.
- Si vous voulez savoir ce qui se cache derrière une commande ``make``, ouvrez le fichier nommé ``Makefile`` présent à la racine du projet.
- Si une erreur s'est glissée dans la doc, ou si la doc a glissé vers l'obscolescence, ouvrez `un ticket sur notre repo github <https://github.com/zestedesavoir/zds-site/issues/new>`_
- Si malgré tout vous ne parvenez pas à installer ZdS, n'hésitez pas à ouvrir `un sujet sur le forum <https://zestedesavoir.com/forums/sujet/nouveau/?forum=2>`_

Certaines des commandes d'installation (débutant par ``apt-get``) sont données ici pour Debian et ses dérivés, pour lesquels il est sûr qu'elles fonctionnent. Si vous utilisez une distribution différente, le nom des paquets à installer devrait être fort semblable, n'hésitez dès lors pas à employer la fonction "recherche" de votre gestionnaire de paquet préféré. Les autres commandes sont génériques et indépendantes de la distribution utilisée.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

ZdS a besoin des dépendances suivantes, installables manuellement ou à l'aide d'un Makefile (voir plus bas) :

- git : ``apt-get install git``
- python3 et python3-dev : ``apt-get install python3-dev``
- setuptools : ``apt-get install python3-setuptools``
- pip : ``apt-get install python3-pip``
- libxml2-dev : ``apt-get install libxml2-dev``
- python-lxml : ``apt-get install python3-lxml``
- libxlst-dev (peut être appelée libxlst1-dev sur certains OS comme Ubuntu)
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse : ``apt-get install python3-sqlparse``
- libffi : ``apt-get install libffi-dev``
- libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev : ``apt-get install libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev`` (peut être appelée libjpeg8 et libjpeg8-dev sur  certains OS comme Ubuntu)
- gcc : ``apt-get install build-essential``

Ou à l'aide du Makefile (``sudo`` sera appelé automatiquement, ne l'ajoutez jamais si on ne le précise pas) :

Pour Debian.

.. sourcecode:: bash

    make install-debian

Pour Ubuntu.

.. sourcecode:: bash

    make install-ubuntu

Pour Fedora.

.. sourcecode:: bash

    make install-fedora

Pour Archlinux.

.. sourcecode:: bash

   make install-archlinux

Installation et configuration de `virtualenv`
=============================================

(cette étape n'est pas obligatoire mais fortement conseillée; ne tapez PAS les commandes en root donc pas avec ``sudo``)

.. sourcecode:: bash

    pip3 install --user virtualenv # Ajout du module virtualenv
    virtualenv zdsenv --python=python3 # Création du répertoire "zdsenv"


**À chaque fois** que vous souhaitez travailler dans votre environnement, activez-le via la commande suivante :

.. sourcecode:: bash

    source zdsenv/bin/activate # PAS sudo


Pour sortir de votre environnement, tapez ``deactivate``

Une documentation plus complète de cet outil `est disponible ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Lancer ZdS
==========

Une fois dans votre environnement python (``source ../bin/activate`` si vous utilisez virtualenv, très fortement conseillé), lancez l'installation complète (commandes à taper sans être sudo dans le répertoire du clone de votre fork, l'environnement Python devant être activé) :

.. sourcecode:: bash


    make install-back # Dépendances Python
    make migrate # Cf. "migrate" de Django
    make run-back # Démarre l'instance de ZdS

**NB** : Vérifiez bien que votre interpréteur par défaut utilise Python 3 et non une version 2.x.


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble (ceci n'est pas obligatoire) vous pouvez installer les outils LateX,
Pandoc et les polices Microsoft.
Ce qui revient à lancer les commmandes suivantes :

.. sourcecode:: bash

    apt-get install --reinstall ttf-mscorefonts-installer
    apt-get install texlive texlive-xetex texlive-lang-french texlive-latex-extra
    apt-get install haskell-platform
    cabal update
    cabal install pandoc

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
