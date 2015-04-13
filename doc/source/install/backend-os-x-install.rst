=================================
Installation du backend sous OS X
=================================

Pour installer une version locale de ZdS sur OS X, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Avant de vous lancez dans l'installation de l'environnement de zds, il faut quelques pré-requis :

- Installer `XCode <http://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12>`_ pour pouvoir exécuter des commandes (g)cc.
- Installer `MacPorts <http://www.macports.org/>`_ pour récupérer certains paquets utiles pour l'installation des dépendances de ce projet.
- Installer python 2.7
- Installer pip
- Installer git
- Installer `gettext <https://www.gnu.org/software/gettext/>`_

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds.

Installation de virtualenv
==========================

.. sourcecode:: bash

    sudo port install virtualenv_select py27-virtualenv py27-virtualenvwrapper py27-tox

    mkdir ~/.virtualenvs
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile && export WORKON_HOME=$HOME/.virtualenvs
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile && source /usr/local/bin/virtualenvwrapper.sh


Création de votre environnement
===============================

.. sourcecode:: bash

    mkvirtualenv zdsenv


Récupération de la librairie lxml pour python 2.7 via MacPorts
==============================================================

.. sourcecode:: bash

  sudo port install py27-lxml

Récupération de la cairo (svg) via Homebrew
==============================================================

.. sourcecode:: bash

  brew install cairo --without-x11


Ajout de flags pour compiler avec gcc plutôt que clang lors de l'installation de lxml
=====================================================================================

.. sourcecode:: bash

  export CFLAGS=-Qunused-arguments
  export CPPFLAGS=-Qunused-arguments


Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Installation de toutes les dépendances
======================================

.. sourcecode:: bash

  pip install --upgrade -r requirements.txt -r requirements-dev.txt
  npm install
  gulp build


Pour relancer votre environnement : ``source ~/.virtualenvs/zdsenv/bin/activate``
Pour sortir de votre environnement : ``deactive``

Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez `BasicTex <http://www.tug.org/mactex/morepackages.html>`_

.. sourcecode:: bash

  sudo port install texlive-basic

- Téléchargez et installez `Pandoc <https://github.com/jgm/pandoc/releases>`_

.. sourcecode:: bash

  sudo port install pandoc


Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <utils/git-pre-hook.html>`__.
