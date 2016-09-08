==================================
Installation du backend sous macOS
==================================

Pour installer une version locale de ZdS sur macOS, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Avant de vous lancez dans l'installation de l'environnement de zds, il faut quelques pré-requis :

- Installer `XCode <http://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12>`_ pour pouvoir exécuter des commandes (g)cc.
- Installer `Homebrew <http://brew.sh/>`_ pour récupérer certains paquets utiles pour l'installation des dépendances de ce projet.
- Installer python 2.7
- Installer pip
- Installer git
- Installer `gettext <https://www.gnu.org/software/gettext/>`_
- Installer GeoIP (``brew install geoip``)

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds.

Installation de virtualenv
==========================

.. sourcecode:: bash

    make install-osx

    mkdir ~/.virtualenvs
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile && export WORKON_HOME=$HOME/.virtualenvs
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile && source /usr/local/bin/virtualenvwrapper.sh


Création de votre environnement
===============================

.. sourcecode:: bash

    mkvirtualenv zdsenv


Récupération de cairo (svg)
===========================

.. sourcecode:: bash

  brew install cairo --without-x11
  brew install py2cairo # py3cairo quand ZdS sera en python 3


Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Sur macOS, ``brew install node`` suffit pour installer Node.js

Installation de toutes les dépendances
======================================

.. sourcecode:: bash

  make install-back
  make install-front


Pour relancer votre environnement : ``source ~/.virtualenvs/zdsenv/bin/activate``.

Si vous avez installé virtualenvwrapper, vous pouvez utiliser le raccourcis ``workon zdsenv``.

Pour sortir de votre environnement : ``deactivate``.

Lancer ZdS
==========

Une fois dans votre environnement python et toutes les dépendances installées, lançons ZdS :

.. sourcecode:: bash

    make migrate
    make run-back

Aller plus loin
===============

.. Attention::

    Cette section n'a jamais été testée. Si vous êtes parvenu à installer Latex et Pandoc et à les faire fonctionner avec ZdS, toute contribution à cette documentation est largement la bienvenue !

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez `BasicTex <http://www.tug.org/mactex/morepackages.html>`_

.. sourcecode:: bash

  brew install texlive-basic

- Téléchargez et installez `Pandoc <https://github.com/jgm/pandoc/releases>`_

.. sourcecode:: bash

  brew install pandoc


Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
