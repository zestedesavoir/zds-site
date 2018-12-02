=======================
Installation sous macOS
=======================

.. Attention::

    Cette partie de la documentation n'est probablement pas à jour faute de contributeur utilisant MacOS. Il se peut que l'installation et les tests unitaires fonctionnent correctement, partiellement ou pas du tout. Bref, en cas de problème n'hésitez pas à venir demander de l'aide sur le `forum des Devs' de Zeste de Savoir <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ !

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

  brew install gettext cairo --without-x11 py2cairo node && \
  pip3 install virtualenv virtualenvwrapper

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

On installe `les outils du front-end <extra-install-frontend.html>`_, `zmarkdown <extra-zmd.html>`_ puis les packages python:

.. sourcecode:: bash

  make install-front
  make build-front
  make zmd-install
  make install-back

Lancer ZdS
==========

Une fois dans votre environnement python et toutes les dépendances installées, lançons ZdS.
On crée d'abord la base de donnée, puis le `jeu de données utile au dévellopement <../utils/fixture_loaders.html>`_:

.. sourcecode:: bash

    make migrate-db
    make generate-fixtures

On peut finalement lancer zmarkdown, puis ZdS:

.. sourcecode:: bash

    make zmd-start
    make run-back


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Elasticsearch:

- `Installez Elasticsearch <extra-install-es.html>`_ ;
- `Installez LaTeX <extra-install-latex.html>`_.

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
