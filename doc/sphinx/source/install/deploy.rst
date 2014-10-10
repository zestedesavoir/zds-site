Configuration des serveurs
==========================

Zeste de Savoir est installe en 1 tiers (sur un seul serveur donc).

Paramètres généraux
-------------------

+------------------------+----------------------------+
| Paramètre              | Valeur                     |
+========================+============================+
| OS                     | Linux, Debian 7 “Wheezy”   |
+------------------------+----------------------------+
| Serveurs web           | Nginx                      |
+------------------------+----------------------------+
| Moteur WSGI            | Gunicorn                   |
+------------------------+----------------------------+
| SGBD                   | MySQL                      |
+------------------------+----------------------------+
| Contrôle des process   | Supervisor                 |
+------------------------+----------------------------+
| Surveillance           | Munin                      |
+------------------------+----------------------------+

Paramètres spécifiques
----------------------

+----------------+-----------------------------+-----------------------------+
| Pré-prod       | Prod                        |
+================+=============================+=============================+
| Nom            | preprod.zestedesavoir.com   | zestedesavoir.com           |
+----------------+-----------------------------+-----------------------------+
| IPv4           | ``178.32.53.245``           | -                           |
+----------------+-----------------------------+-----------------------------+
| IPv6           | ``176.31.187.88``           | ``2001:41d0:52:100::b4f``   |
+----------------+-----------------------------+-----------------------------+
| Login          | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+
| Mot de passe   | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+

Premier déploiement
===================

Toute la procédure suppose un dépoiement dans ``/opt/zdsenv``.

Installation des outils
-----------------------

-  python,
-  virtualenv (dans /opt/zdsenv/),
-  git

Clone du repo et configuration de prod
--------------------------------------

-  ``git clone https://github.com/zestedesavoir/zds-site.git``
-  ``mkdir tutoriels-private``
-  ``mkdir tutoriels-public``
-  ``mkdir articles-data``
-  ``touch zds/settings_prod.py``
-  ``vim zds/settings_prod.py``

On édite le fichier de manière à rajouter les infos spécifiques au
serveur courant. Par exemple :

.. code:: text

    DEBUG = False

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'zdsdb',
            'USER': 'zds',
            'PASSWORD': 'mot_de_passe',
            'HOST': 'localhost',
            'PORT': '',
        }
    }

    EMAIL_HOST = 'mail.geoffreycreation.com'
    EMAIL_HOST_USER = 'zds@geoffreycreation.com'
    EMAIL_HOST_PASSWORD = 'mot_de_passe'
    EMAIL_PORT = 25

Installation de l’application de base
-------------------------------------

Suivre `l’installation complète sous Linux`_ en tenant compte des
subtilités suivantes :

-  Installer `les outils front`_ (l’installation rapide suffit)
-  Ne pas lancer le serveur à la fin de l’étape *“Lancer ZdS”*
-  Installer toutes les dépendances requises à l’étape *“Aller plus
   loin”*

Outils spécifiques à un serveur de run
--------------------------------------

Utilisateur local
~~~~~~~~~~~~~~~~~

Zeste de Savoir tourne sous l’utilisateur **zds** et le groupe **root**.

Gunicorn
~~~~~~~~

Installer Gunicorn dans le virtualenv.

Dans ``/opt/zdsenv/unicorn_start`` :

.. code:: shell

    #!/bin/bash

    NAME="ZesteDeSavoir"
    DJANGODIR=/opt/zdsenv/ZesteDeSavoir/
    SOCKFILE=/opt/zdsenv/bin/gunicorn.sock
    USER=zds
    GROUP=root
    NUM_WORKERS=7 # how many worker processes
    DJANGO_SETTINGS_MODULE=zds.settings # django settings file
    DJANGO_WSGI_MODULE=zds.wsgi # WSGI modul

    echo "Starting $NAME"

    # Activate the virtual environment
    cd $DJANGODIR
    source ../bin/activate
    export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
    export PYTHONPATH=$DJANGODIR:$PYTHONPATH

    RUNDIR=$(dirname $SOCKFILE)
    test -d $RUNDIR || mkdir -p $RUNDIR

    exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --user=$USER --group=$GROUP \
    --log-level=debug \
    --timeout=300 \
    --bind=unix:$SOCKFILE

Nginx
~~~~~

Installer nginx. Sous Debian, la configuration est splittée par site.
Pour Zeste de Savoir elle se fait dans
``/etc/nginx/sites-available/zestedesavoir`` :

\`\`\`text upstream zdsappserver { server unix:/opt

.. _l’installation complète sous Linux: install-linux.md
.. _les outils front: gulp.md