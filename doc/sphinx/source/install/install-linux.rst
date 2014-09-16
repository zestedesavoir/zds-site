=======================
Installation sous Linux
=======================

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Les commandes suivantes sont génériques et indépendantes de la distribution que vous utilisez.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

Assurez vous que les dépendances suivantes soient résolues :

- git : ``apt-get install git``
- python2.7
- python-dev : ``apt-get install python-dev``
- easy_install : ``apt-get install python-setuptools``
- pip : ``easy_install pip``
- libxml2-dev : ``apt-get install libxml2-dev``
- python-lxml : ``apt-get install python-lxml``
- libxlst-dev (peut être appelée libxlst1-dev sur certains OS comme ubuntu
- libz-dev (peut être libz1g-dev sur système 64bits)
- python-sqlparse
- libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev : ``apt-get install libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev``

Ou, en une ligne,

.. sourcecode:: bash

    apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev
    easy_install pip

Instalation et configuration de `virtualenv`
============================================

(cette étape n'est pas obligatoire, mais fortement conseillée)

.. sourcecode:: bash

    pip install virtualenv
    virtualenv zdsenv --python=python2


**À chaque fois** que vous souhaitez travailler dans votre environement, activez le via la commande suivante :

.. sourcecode:: bash

    source zdsenv/bin/activate


Pour sortir de votre environnement : ``deactive``

Une documentation plus complète de cet outil `est disponible ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

Front ou Back ?
===============

Si vous ne comptez qu'au back-end du site, téléchargez le zip des ressources `ici <http://zestedesavoir.com/static/pack.zip>`_
Il faudra l'extraire dans le dossier ``dist/`` à la racine de votre projet.

Si vous comptez contribuer au front-end, rendez-vous sur [la documentation dédiée](gulp.md).

Lancer ZdS
==========

Une fois dans votre environnement python (``source ../bin/activate`` si vous utilisez virtualenv, très fortement conseillé), lancez l'installation complète :

.. sourcecode:: bash

    pip install --upgrade -r requirements.txt
    python manage.py syncdb
    python manage.py migrate
    python manage.py runserver


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble (ceci n'est pas obligatoire) vous pouvez installer les outils LateX, Pandoc et les polices Microsoft. Ce qui revient à lancer les commmandes suivantes :

.. sourcecode:: bash

    apt-get install --reinstall ttf-mscorefonts-installer
    apt-get install texlive texlive-xetex texlive-lang-french texlive-latex-extra
    apt-get install haskell-platform
    cabal update
    cabal install pandoc

