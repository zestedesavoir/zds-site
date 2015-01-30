========================================
Configuration des serveurs de production
========================================

Zeste de Savoir est installé en 1 tiers (sur un seul serveur donc).

Paramètres
==========

Paramètres généraux
-------------------

+------------------------+----------------------------+
| Paramètre              | Valeur                     |
+========================+============================+
| OS                     | Linux, Debian 7 "Wheezy"   |
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
|                | Préproduction               | Production                  |
+================+=============================+=============================+
| Nom            | beta.zestedesavoir.com      | zestedesavoir.com           |
+----------------+-----------------------------+-----------------------------+
| IPv4           | ``46.105.246.77``           | ``176.31.187.88``           |
+----------------+-----------------------------+-----------------------------+
| IPv6           | x                           | ``2001:41d0:52:100::b4f``   |
+----------------+-----------------------------+-----------------------------+
| Identifiant    | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+
| Mot de passe   | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+

Premier déploiement
===================

Toute la procédure suppose un déploiement dans ``/opt/zdsenv``.

Utilisateur local
-----------------

Zeste de Savoir tourne sous l'utilisateur **zds** et le groupe **root**.

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
-  ``vim zds/settings_prod.py``

On édite le fichier de manière à rajouter les infos spécifiques au serveur courant. Par exemple :

.. code:: python

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

Installation de l'application de base
-------------------------------------

Suivre `l'installation complète sous Linux <backend-linux-install.html>`__ en tenant compte des subtilités suivantes :

-  Installer `les outils front <frontend-install.md>`__
-  Ne pas lancer le serveur à la fin de l'étape *"Lancer ZdS"*
-  Installer toutes les dépendances requises à l'étape *"Aller plus loin"*

Outils spécifiques à un serveur de run
--------------------------------------

Gunicorn
~~~~~~~~

Installer Gunicorn dans le virtualenv.

Dans ``/opt/zdsenv/unicorn_start`` :

.. code:: bash

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

Installer nginx. Sous Debian, la configuration est splittée par site. Pour Zeste de Savoir, elle se fait dans ``/etc/nginx/sites-available/zestedesavoir`` :

.. code:: text

    upstream zdsappserver {
        server unix:/opt/zdsenv/bin/gunicorn.sock fail_timeout=0;
    }
    server {
        server_name www.zestedesavoir.com;
        rewrite ^(.*) http://zestedesavoir.com$1 permanent;
    }
    server {
        listen [::]:80 ipv6only=on;
        listen 80;

        listen 443 ssl;
        ssl_certificate /etc/ssl/certs/zds/server.crt;
        ssl_certificate_key /etc/ssl/certs/zds/server.key;
        ssl_protocols SSLv3 TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers HIGH:!aNULL:!MD5;

        server_name zestedesavoir.com;
        gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;
        access_log off;
        access_log /opt/zdsenv/logs/nginx-access.log;
        error_log /opt/zdsenv/logs/nginx-error.log;

        location = /robots.txt {
            alias /opt/zdsenv/ZesteDeSavoir/robots.txt ;
        }

        location /static/admin/ {
            alias /opt/zdsenv/lib/python2.7/site-packages/django/contrib/admin/static/admin/;
        }

        location /static/ {
            alias /opt/zdsenv/ZesteDeSavoir/static/;
            expires 1d;
            add_header Pragma public;
            add_header Cache-Control "public, must-revalidate, proxy-revalidate";
        }

        location /media/ {
            alias /opt/zdsenv/ZesteDeSavoir/media/;
            expires 1d;
            add_header Pragma public;
            add_header Cache-Control "public, must-revalidate, proxy-revalidate";
        }

        location / {
                #if ($http_host ~* "^www\.(.+)$"){
                    #rewrite ^(.*)$ http://%1$request_uri redirect;
                #}
                if ($uri !~ \. ){
                    rewrite ^(.*[^/])$ $1/ permanent;
                }
                client_max_body_size 100M;
                proxy_read_timeout 1000s;
                proxy_connect_timeout 1000s;
                auth_basic "Qui es-tu noble etranger ?";
                auth_basic_user_file  /home/zds/.htpasswdclose;
                ####proxy_pass http://176.31.187.88:8001;
                proxy_set_header X-Forwarded-Host $server_name;
                proxy_set_header X-Forwaded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header REMOTE_ADDR $remote_addr;
                add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
                if (!-f $request_filename) {
                    proxy_pass http://zdsappserver;
                    break;
                }

          }
        # Error pages
        error_page 500 502 503 504 /500.html;
        location = /500.html {
            root /opt/zdsenv/ZesteDeSavoir/templates/;
        }
    }

Solr
~~~~

`Voir la documentation de Solr <install-solr.html>`.

Supervisor
~~~~~~~~~~

Installer supervisor.

Créer deux configurations :

Configuration ZdS
^^^^^^^^^^^^^^^^^

La conf dans ``/etc/supervisor/conf.d/zds.conf`` permet de lancer Solr à l'aide de ``supervisorctl start zds`` et l'arrêter avec ``supervisorctl stop zds``.

.. code:: text

    [program:zds]
    command = /opt/zdsenv/unicorn_start ;
    user = zds ;
    stdout_logfile = /opt/zdsenv/logs/gunicorn_supervisor.log ;
    redirect_stderr = true ;

Configuration Solr
^^^^^^^^^^^^^^^^^^

La conf dans ``/etc/supervisor/conf.d/solr.conf`` permet de lancer Solr à l'aide de ``supervisorctl start solr`` et l'arrêter avec ``supervisorctl stop solr``.

.. code:: text

    [program:solr]
    command=java -jar start.jar
    autostart=true
    autorestart=true
    stderr_logfile=/opt/zdsenv/logs/solr.err.log
    stdout_logfile=/opt/zdsenv/logs/solr.out.log

Munin
~~~~~

Configuration générale
^^^^^^^^^^^^^^^^^^^^^^

Installer le noeud Munin : ``apt-get install munin-node``.

On obtient les suggestions de plugins à installer avec ``munin-node-configure --suggest`` et les commandes à lancer pour les activer via ``munin-node-configure --shell``.

Pour l'instant le serveur de graphe est fourni par SpaceFox et `est visible ici <http://munin.kisai.info>`__. Seul SpaceFox peut mettre à jour cette configuration. Le serveur de graphe accède au serveur en SSH avec cette clé publique :

.. code:: text

    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBsfYaz5d4wtyTM0Xx1TjpJt0LuZ2Il9JZD2+s4hNQToNBaqT3aafG1SuHuQkqjvIQrI28NEkjALQIp4zD7BOeeW9QlAwE7uiebi3FcwLfaPFwq5qvnpyOSmbktCjHX24a14ozgDPY5diPkOsyMdEYz/KTybSvFvgUjzUSCLBQ2EWj0CBktY6cFC45pvVCsdd/ToDsEVbhixyNmlOMc+FB/oT8CC6ZoDezSXQGaO51/zLS8l4ieBIcB4tK3JdJI+fFv5FJsfgMK+DbNV4pikw9qEZJlASQCU69L+YR7MxTXNCqRyQ1Z4qxH4ZdPELmNOoMB8dHxxBX7TGP+Hvpm3AH munin@Yog-Sothoth

Configuration spécifique à ZdS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Créer les liens vers le plugin Django-Munin :

.. code:: bash

    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_active_sessions
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_active_users
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_db_performance
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_articles
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_mps
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_posts
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_sessions
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_topics
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_tutorials
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_users

Ajouter les métriques suivantes au fichier ``/etc/munin/plugin-conf.d/munin-node`` :

.. code:: text

    [zds_db_performance]
    env.url http://zestedesavoir.com/munin/db_performance/
    env.graph_category zds

    [zds_total_users]
    env.url http://zestedesavoir.com/munin/total_users/
    env.graph_category zds

    [zds_active_users]
    env.url http://zestedesavoir.com/munin/active_users/
    env.graph_category zds

    [zds_total_sessions]
    env.url http://zestedesavoir.com/munin/total_sessions/
    env.graph_category zds

    [zds_active_sessions]
    env.url http://zestedesavoir.com/munin/active_sessions/
    env.graph_category zds

    [zds_total_topics]
    env.url http://www.zestedesavoir.com/munin/total_topics/
    env.graph_category zds

    [zds_total_posts]
    env.url http://www.zestedesavoir.com/munin/total_posts/
    env.graph_category zds

    [zds_total_mps]
    env.url http://www.zestedesavoir.com/munin/total_mps/
    env.graph_category zds

    [zds_total_tutorials]
    env.url http://www.zestedesavoir.com/munin/total_tutorials/
    env.graph_category zds

    [zds_total_articles]
    env.url http://www.zestedesavoir.com/munin/total_articles/
    env.graph_category zds

Mise à jour d'une instance existante
====================================

`Allez jeter un coup d'oeil à notre script de déploiement <https://github.com/zestedesavoir/zds-site/blob/dev/server/deploy.sh>` ! ;)

Personnalisation d'une instance
===============================

Il est possible de personnaliser ZdS pour n'importe quel site communautaire de partage. Un ensemble de paramètres est disponible dans le fichier ``settings.py`` via un dictionnaire. Vous pourrez donc écraser ces variables par défaut dans votre fichier ``settings_prod.py``. Le dictionnaire de variables relatives au site est donc le suivant :

.. sourcecode:: python

    ZDS_APP = {
        'site': {
            'name': u"ZesteDeSavoir",
            'litteral_name': u"Zeste de Savoir",
            'slogan': u"Zeste de Savoir, la connaissance pour tous et sans pépins",
            'abbr': u"zds",
            'url': u"http://127.0.0.1:8000",
            'dns': u"zestedesavoir.com",
            'email_contact': u"communication@zestedesavoir.com",
            'email_noreply': u"noreply@zestedesavoir.com",
            'repository': u"https://github.com/zestedesavoir/zds-site",
            'short_description': u"",
            'long_description': u"Zeste de Savoir est un site de partage de connaissances "
                                u"sur lequel vous trouverez des tutoriels de tous niveaux, "
                                u"des articles et des forums d'entraide animés par et pour "
                                u"la communauté.",
            'year': u"2014",
            'association': {
                'name': u"Zeste de Savoir",
                'fee': u"30 €",
                'email': u"association@zestedesavoir.com",
                'email_ca': u"ca-zeste-de-savoir@googlegroups.com"
            },
            'licenses': {
                'logo': {
                    'code': u"CC-BY",
                    'title': u"Creative Commons License",
                    'description': u"Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - "
                                u"Partage dans les Mêmes Conditions 4.0 International.",
                    'url_image': u"http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                    'url_license': u"http://creativecommons.org/licenses/by-nc-sa/4.0/",
                    'author': u"MaxRoyo"
                },
                'cookies': {
                    'code': u"CC-BY",
                    'title': u"Licence Creative Commons",
                    'description': u"licence Creative Commons Attribution 4.0 International",
                    'url_image': u"http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                    'url_license': u"http://creativecommons.org/licenses/by-nc-sa/4.0/"
                },
                'source': {
                    'code': u"GPL v3",
                    'url_license': u"http://www.gnu.org/licenses/gpl-3.0.html",
                    'provider_name': u"Progdupeupl",
                    'provider_url': u"http://progdupeu.pl",
                },
                'licence_info_title': u'http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-licences-sur-zeste-de-savoir/',
                'licence_info_link': u'Le droit d\'auteur, Creative Commons et les licences sur Zeste de Savoir'
            },
            'hosting': {
                'name': u"OVH",
                'address': u"2 rue Kellermann - 59100 Roubaix - France"
            },
            'social': {
                'facebook': u'https://www.facebook.com/ZesteDeSavoir',
                'twitter': u'https://twitter.com/ZesteDeSavoir',
                'googleplus': u'https://plus.google.com/u/0/107033688356682807298'
            },
            'cnil': u"1771020",
        },
        'member': {
            'bot_account': u"admin",
            'anonymous_account': u"anonymous",
            'external_account': u"external",
            'bot_group': u'bot',
            'members_per_page': 100,
        },
        'gallery': {
            'image_max_size': 1024 * 1024,
        },
        'article': {
            'home_number': 5,
            'repo_path': os.path.join(SITE_ROOT, 'articles-data')
        },
        'tutorial': {
            'repo_path': os.path.join(SITE_ROOT, 'tutoriels-private'),
            'repo_public_path': os.path.join(SITE_ROOT, 'tutoriels-public'),
            'default_license_pk': 7,
            'home_number': 5,
            'helps_per_page': 20
        },
        'forum': {
            'posts_per_page': 21,
            'topics_per_page': 21,
            'spam_limit_seconds': 60 * 15,
            'spam_limit_participant': 2,
            'followed_topics_per_page': 21,
            'beta_forum_id': 1,
            'max_post_length': 1000000,
            'top_tag_max': 5,
        },
        'paginator':{
            'folding_limit': 4
        }
    }
