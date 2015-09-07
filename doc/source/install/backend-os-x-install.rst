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
- Installer GeoIP (``brew install geoip``)

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds.

Installation de virtualenv
==========================

.. sourcecode:: bash

    sudo port install virtualenv_select py27-virtualenv py27-virtualenvwrapper py27-tox

    mkdir ~/.virtualenvs
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile && export WORKON_HOME=$HOME/.virtualenvs
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile && source /usr/local/bin/virtualenvwrapper.sh

.. Attention::

    Il se peut que MacPorts ne vous installe pas virtualenvwrapper dans /usr/local/bin. Si ça diffère, pensez à mettre à jour la commande avec le chemin que MacPorts à utilisé.


Création de votre environnement
===============================

.. sourcecode:: bash

    mkvirtualenv zdsenv


Récupération de la librairie lxml pour python 2.7 via MacPorts
==============================================================

.. sourcecode:: bash

  sudo port install py27-lxml

Récupération de cairo (svg)
===========================

Il existe 2 moyens d'installer cairo sur votre système. L'un avec Homebrew, l'autre avec MacPorts. Dans un premier temps, tentez d'installer cairo avec homebrew. Si ça ne fonctionne pas, désinstallez les dépendances Homebrew et tentez l'installation avec MacPorts.

.. sourcecode:: bash

  brew install cairo --without-x11
  brew install py2cairo # py3cairo quand ZdS sera en python 3

.. sourcecode:: bash

  sudo port install cairo


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


Pour relancer votre environnement : ``source ~/.virtualenvs/zdsenv/bin/activate``.

Si vous avez installé virtualenvwrapper, vous pouvez utiliser le raccourcis ``workon zdsenv``.

Pour sortir de votre environnement : ``deactive``.

Lancer ZdS
==========

Une fois dans votre environnement python et toutes les dépendances installées, lançons ZdS :

.. sourcecode:: bash

    python manage.py migrate
    python manage.py runserver

Aller plus loin
===============

.. Attention::

    Cette section n'a jamais été testée. Si vous êtes parvenu à installer Latex et Pandoc et à les faire fonctionner avec ZdS, toute contribution à cette documentation est largement la bienvenue !

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez `BasicTex <http://www.tug.org/mactex/morepackages.html>`_

.. sourcecode:: bash

  sudo port install texlive-basic

- Téléchargez et installez `Pandoc <https://github.com/jgm/pandoc/releases>`_

.. sourcecode:: bash

  sudo port install pandoc


Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <utils/git-pre-hook.html>`__.
