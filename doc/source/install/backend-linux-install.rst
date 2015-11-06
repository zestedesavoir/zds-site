==================================
Installation du backend sous Linux
==================================

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Certaines des commandes d'installation (débutant par ``apt-get``) sont données ici pour Debian et ses dérivés, pour lesquels il est sûr qu'elles fonctionnent. Néanmoins, si vous utilisez une distribution différente, le nom des paquets à installer devrait être fort semblable, n'hésitez dès lors pas à employer la fonction "recherche" de votre gestionnaire de paquet préféré. Les autres commandes sont génériques et indépendantes de la distribution utilisée.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

Assurez vous que les dépendances suivantes soient résolues :

- git : ``apt-get install git``
- python2.7
- python-dev : ``apt-get install python-dev``
- easy_install : ``apt-get install python-setuptools``
- pip : ``easy_install pip``
- tox : ``pip install tox``
- libgeoip-dev : ``apt-get install libgeoip-dev``
- libxml2-dev : ``apt-get install libxml2-dev``
- python-lxml : ``apt-get install python-lxml``
- libxlst-dev (peut être appelée libxlst1-dev sur certains OS comme ubuntu
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse
- libffi : ``apt-get install libffi-dev``
- libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev : ``apt-get install libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev``

Ou, en une ligne :

Pour Ubuntu.

.. sourcecode:: bash

    sudo apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev libffi-dev python-pip python-tox # Dépendances du projet

Pour Fedora.

.. sourcecode:: bash

    sudo dnf install git python-devel python-setuptools libxml2-devel python-lxml libxslt-devel zlib-devel python-sqlparse libjpeg-turbo-devel libjpeg-turbo-devel freetype freetype-devel libffi-devel python-pip python-tox # Dépendances du projet

Installation et configuration de `virtualenv`
=============================================

(cette étape n'est pas obligatoire, mais fortement conseillée)

.. sourcecode:: bash

    pip install --user virtualenv # Ajout du module virtualenv - ne PAS être sudo
    virtualenv zdsenv --python=python2 # Création du répertoire "zdsenv" - ne PAS être sudo


**À chaque fois** que vous souhaitez travailler dans votre environnement, activez le via la commande suivante :

.. sourcecode:: bash

    source zdsenv/bin/activate # Ne PAS être sudo


Pour sortir de votre environnement : ``deactivate``

Une documentation plus complète de cet outil `est disponible ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Lancer ZdS
==========

Une fois dans votre environnement python (``source ../bin/activate`` si vous utilisez virtualenv, très fortement conseillé), lancez l'installation complète :

.. sourcecode:: bash

    pip install --upgrade -r requirements.txt -r requirements-dev.txt # Installe les dépendances Python (--upgrade = permet de mettre à jour les fichiers si et seulement si qq a màj les fichiers requirements) - Ne PAS être sudo, à faire dans le répertoire du clone de votre fork, activation de l'environnement Python requise)
    python manage.py migrate # Cf. migrate de Django (le faire à l'installation et à la mise à jour) - Ne PAS être sudo, à faire dans le répertoire du clone de votre fork, activation de l'environnement Python requise
    python manage.py runserver # Démarre l'instance de ZdS - Ne PAS être sudo, à faire dans le répertoire du clone de votre fork, activation de l'environnement Python requise
    deactivate


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
