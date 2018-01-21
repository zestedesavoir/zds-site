==================================
Installation du backend sous macOS
==================================

Pour installer une version locale de ZdS sur macOS, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Pré-requis
==========

- Installer XCode :

.. sourcecode:: bash

  xcode-select --install

- Installer `Homebrew <http://brew.sh/>`_.
- Installer un nouveau Python par Homebrew :

.. sourcecode:: bash

  brew install python --framework
  # Il se peut que votre système n'utilise pas la nouvelle version de Python. Si c'est le cas, lancez la commande suivante.
  export PATH=/usr/local/bin:/usr/local/sbin:${PATH}

- Si vous avez décidé de ne pas installer un nouveau python et que vous utilisez celui de base du système, installez pip :

.. sourcecode:: bash

  wget https://bootstrap.pypa.io/get-pip.py
  python3 get-pip.py

- Installer toutes les dépendances systèmes nécessaires :

.. sourcecode:: bash

  make install-macos

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds.

Configuration de virtualenv
===========================

(Si vous n'utilisez pas bash mais un autre shell, par exemple zsh, remplacez ``~/.bash_profile`` par le fichier rc de votre shell, par exemple ``~/.zshrc``.)

.. sourcecode:: bash

  mkdir ~/.virtualenvs
  echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile
  echo "source /usr/local/Cellar/python3/3*/Frameworks/Python.framework/Versions/3.*/bin/virtualenvwrapper.sh" >> ~/.bash_profile
  source ~/.bash_profile

Usage de virtualenv
===================

Création d'un virtualenv :

.. sourcecode:: bash

  mkvirtualenv -p python3 zdsenv

Lancer un virtualenv :

.. sourcecode:: bash

  workon zdsenv

Quitter un virtualenv :

.. sourcecode:: bash

  deactivate


Installation des des dépendances front et back
==============================================

.. sourcecode:: bash

  make install-front
  make build-front
  make install-back

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


Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
