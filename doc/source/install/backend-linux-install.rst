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
- geoip : ``apt-get install geoip`` (peut s'appeler ``geoip-bin`` sur certaines distributions telles que Debian)
- libgeoip-dev : ``apt-get install libgeoip-dev``
- libxml2-dev : ``apt-get install libxml2-dev``
- python-lxml : ``apt-get install python-lxml``
- libxlst-dev (peut être appelée libxlst1-dev sur certains OS comme ubuntu
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse
- libffi : ``apt-get install libffi-dev``
- libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev : ``apt-get install libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev``

Ou, en une ligne,

.. sourcecode:: bash

    apt-get install git python-dev python-setuptools '^geoip(-bin)?$' libgeoip-dev libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev libffi-dev
    easy_install pip tox

Installation et configuration de `virtualenv`
=============================================

(cette étape n'est pas obligatoire, mais fortement conseillée)

.. sourcecode:: bash

    pip install virtualenv
    virtualenv zdsenv --python=python2


**À chaque fois** que vous souhaitez travailler dans votre environement, activez le via la commande suivante :

.. sourcecode:: bash

    source zdsenv/bin/activate


Pour sortir de votre environnement : ``deactive``

Une documentation plus complète de cet outil `est disponible ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Lancer ZdS
==========

Une fois dans votre environnement python (``source ../bin/activate`` si vous utilisez virtualenv, très fortement conseillé), lancez l'installation complète :

.. sourcecode:: bash

    pip install --upgrade -r requirements.txt -r requirements-dev.txt
    python manage.py migrate
    python manage.py runserver


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
