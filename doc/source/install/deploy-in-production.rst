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
| OS                     | Linux, Debian 8 "Jessie"   |
+------------------------+----------------------------+
| Serveurs web           | Nginx                      |
+------------------------+----------------------------+
| Moteur WSGI            | Gunicorn                   |
+------------------------+----------------------------+
| SGBD                   | MySQL                      |
+------------------------+----------------------------+
| Contrôle des process   | systemd                    |
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
| IPv4           | ``46.105.246.77``           | ``149.202.54.142``          |
+----------------+-----------------------------+-----------------------------+
| IPv6           | x                           | Pas encore disponible…      |
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

Dans ``/opt/zdsenv/gunicorn_config.py`` :

.. code:: python

    command = '/opt/zdsenv/bin/gunicorn'
    pythonpath = '/opt/zdsenv/ZesteDeSavoir'
    bind = 'unix:/opt/zdsenv/bin/gunicorn.sock'
    workers = 7
    user = 'zds'
    group = 'zds'
    errorlog = '/opt/zdsenv/logs/gunicorn_error.log'
    loglevel = 'info'
    pid = '/opt/zdsenv/gunicorn.pid'


Nginx
~~~~~

Installer nginx. Sous Debian, la configuration est splittée par site. Pour Zeste de Savoir, elle se fait dans ``/etc/nginx/sites-available/zestedesavoir`` :

.. code:: text

    upstream zdsappserver {
         server unix:/opt/zdsenv/bin/gunicorn.sock fail_timeout=0;
    }
    server {
        listen [::]:80;
        listen [::]:443;
        listen 80;
        listen 443 ssl;
        ssl_certificate /etc/ssl/certs/zds/ssl_2015_unified.crt;
        ssl_certificate_key /etc/ssl/certs/zds/ssl_2015.key;
    #    ssl_certificate /etc/ssl/certs/zds/selfgenerated.pem;
    #    ssl_certificate_key /etc/ssl/certs/zds/selfgenerated.key;
        ssl_session_timeout 1d;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK';
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:50m;
        ssl_dhparam /etc/nginx/dhparam.pem;

        server_name www.zestedesavoir.com;
        rewrite ^(.*) $scheme://zestedesavoir.com$1 permanent;
    }
    server {
        listen [::]:80 ipv6only=on;
        listen [::]:443 ssl ipv6only=on;
        listen 80;
        listen 443 ssl;
        ssl_certificate /etc/ssl/certs/zds/ssl_2015_unified.crt;
        ssl_certificate_key /etc/ssl/certs/zds/ssl_2015.key;
    #    ssl_certificate /etc/ssl/certs/zds/selfgenerated.pem;
    #    ssl_certificate_key /etc/ssl/certs/zds/selfgenerated.key;
        ssl_session_timeout 1d;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK';
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:50m;
        ssl_dhparam /etc/nginx/dhparam.pem;

        server_name zestedesavoir.com;
        gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;
        server_tokens off;
        access_log /opt/zdsenv/logs/nginx-access.log;
        error_log /opt/zdsenv/logs/nginx-error.log;

        location /author-files/ {
            index index.html index.php;
            alias /home/zds/tutos_sdzv3/script/;
            #include php.fast.conf;
        }

        location = /robots.txt {
            alias /opt/zdsenv/ZesteDeSavoir/robots.txt;
        }
        # Gandi
        location = /D6BA7D30872A8A72ED225D5601248024.txt {
            alias /opt/zdsenv/ZesteDeSavoir/D6BA7D30872A8A72ED225D5601248024.txt;
        }

        location /static/ {
            alias /opt/zdsenv/ZesteDeSavoir/static/;
            expires 1y;
            add_header Pragma public;
            add_header Cache-Control "public, must-revalidate, proxy-revalidate";
        }

        location /media/ {
            alias /opt/zdsenv/ZesteDeSavoir/media/;
            expires 1y;
            add_header Pragma public;
            add_header Cache-Control "public, must-revalidate, proxy-revalidate";
        }

        location / {
                if ($uri !~ \. ){
                    rewrite ^(.*[^/])$ $1/ permanent;
                }
                rewrite ^/teasing/$ / permanent;
                client_max_body_size 100M;
                sendfile        on;
                keepalive_timeout  0;
                proxy_read_timeout 1000s;
                proxy_connect_timeout 1000s;
                proxy_redirect     off;
                proxy_set_header   Host              $host;
                proxy_set_header   X-Real-IP         $remote_addr;
                proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
                proxy_set_header   X-Forwarded-Proto $scheme;
                proxy_intercept_errors on;

                add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
                add_header Strict-Transport-Security max-age=15768000;
                add_header Access-Control-Allow-Origin *;
                add_header X-Clacks-Overhead "GNU Terry Pratchett";

                if (!-f $request_filename) {
                    proxy_pass http://zdsappserver;
                    break;
                }

          }
        # Error pages
        error_page 500 502 503 504 /errors/500.html;
        #location = /500.html {
        #    root /opt/zdsenv/ZesteDeSavoir/templates/;
        #}
        location /errors/ {
            alias /opt/zdsenv/ZesteDeSavoir/errors/;
        }


        # Conf anti-exploit, source : https://www.howtoforge.com/nginx-how-to-block-exploits-sql-injections-file-injections-spam-user-agents-etc
        ## Block SQL injections
        set $block_sql_injections 0;
        if ($query_string ~ "union.*select.*\(") {
            set $block_sql_injections 1;
        }
        if ($query_string ~ "union.*all.*select.*") {
            set $block_sql_injections 1;
        }
        if ($query_string ~ "concat.*\(") {
            set $block_sql_injections 1;
        }
        if ($block_sql_injections = 1) {
            return 403;
        }

        ## Block file injections
        set $block_file_injections 0;
        if ($query_string ~ "[a-zA-Z0-9_]=http://") {
            set $block_file_injections 1;
        }
        if ($query_string ~ "[a-zA-Z0-9_]=(\.\.//?)+") {
            set $block_file_injections 1;
        }
        if ($query_string ~ "[a-zA-Z0-9_]=/([a-z0-9_.]//?)+") {
            set $block_file_injections 1;
        }
        if ($block_file_injections = 1) {
            return 403;
        }

        ## Block common exploits
        set $block_common_exploits 0;
        if ($query_string ~ "(<|%3C).*script.*(>|%3E)") {
            set $block_common_exploits 1;
        }
        if ($query_string ~ "GLOBALS(=|\[|\%[0-9A-Z]{0,2})") {
            set $block_common_exploits 1;
        }
        if ($query_string ~ "_REQUEST(=|\[|\%[0-9A-Z]{0,2})") {
            set $block_common_exploits 1;
        }
        if ($query_string ~ "proc/self/environ") {
            set $block_common_exploits 1;
        }
        if ($query_string ~ "mosConfig_[a-zA-Z_]{1,21}(=|\%3D)") {
            set $block_common_exploits 1;
        }
        if ($query_string ~ "base64_(en|de)code\(.*\)") {
            set $block_common_exploits 1;
        }
        if ($block_common_exploits = 1) {
            return 403;
        }

        ## Block spam
        set $block_spam 0;
        if ($query_string ~ "\b(ultram|unicauca|valium|viagra|vicodin|xanax|ypxaieo)\b") {
            set $block_spam 1;
        }
        if ($query_string ~ "\b(erections|hoodia|huronriveracres|impotence|levitra|libido)\b") {
            set $block_spam 1;
        }
        if ($query_string ~ "\b(ambien|blue\spill|cialis|cocaine|ejaculation|erectile)\b") {
            set $block_spam 1;
        }
        if ($query_string ~ "\b(lipitor|phentermin|pro[sz]ac|sandyauer|tramadol|troyhamby)\b") {
            set $block_spam 1;
        }
        if ($block_spam = 1) {
            return 403;
        }

        ## Block user agents
        set $block_user_agents 0;

        # Don't disable wget if you need it to run cron jobs!
        #if ($http_user_agent ~ "Wget") {
        #    set $block_user_agents 1;
        #}

        # Disable Akeeba Remote Control 2.5 and earlier
        if ($http_user_agent ~ "Indy Library") {
            set $block_user_agents 1;
        }

        # Common bandwidth hoggers and hacking tools.
        if ($http_user_agent ~ "libwww-perl") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "GetRight") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "GetWeb!") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "Go!Zilla") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "Download Demon") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "Go-Ahead-Got-It") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "TurnitinBot") {
            set $block_user_agents 1;
        }
        if ($http_user_agent ~ "GrabNet") {
            set $block_user_agents 1;
        }
        # SpaceFox: adds HTTrack
        if ($http_user_agent ~ "HTTrack") {
            set $block_user_agents 1;
        }


        if ($block_user_agents = 1) {
            return 403;
        }

    }

    server{
        server_name uploads.zestedesavoir.com;
        root /home/zds/tutos_sdzv3/images_distantes;
        index index.html index.htm;
    }


La configuration de la page de maintenance, quant à elle, se fait dans ``/etc/nginx/sites-available/zds-maintenance`` :

.. code:: text

    server {
        listen [::]:80 ipv6only=on;
        listen [::]:443 ssl ipv6only=on;
        listen 80;
        listen 443 ssl;
        ssl_certificate /etc/ssl/certs/zds/ssl_2015_unified.crt;
        ssl_certificate_key /etc/ssl/certs/zds/ssl_2015.key;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers HIGH:!aNULL:!MD5;

            server_name zestedesavoir.com www.zestedesavoir.com;
            gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript;
            access_log off;
            access_log /opt/zdsenv/logs/nginx-access.log;
            error_log /opt/zdsenv/logs/nginx-error.log;
            root /opt/zdsenv/ZesteDeSavoir;

            location /errors/css {
            }

            location /errors/images {
            }

            location / {
                    return 503;
            }

            error_page 503 @maintenance;
            location @maintenance  {
                    rewrite ^.*$ /errors/maintenance.html break;
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

Les confs dans ``/etc/systemd/system/zds.service`` et ``/etc/systemd/system/zds.socket`` permet de lancer le serveur applicatif de Zeste de Savoir (Gunicorn) à l'aide de ``systemctl start zds.{service,socket}`` et l'arrêter avec ``systemctl stop zds.{service,socket}``.

.. code:: text

    [Unit]
    Description=Zeste de Savoir
    Requires=zds.socket
    After=network.target

    [Service]
    PIDFile=/run/gunicorn/pid
    User=zds
    Group=zds
    WorkingDirectory=/opt/zdsenv
    # ExecStart=/opt/zdsenv/bin/gunicorn --pid /run/gunicorn/pid -c /opt/zdsenv/gunicorn_config.py zds.wsgi
    ExecStart=/opt/zdsenv/bin/gunicorn -c /opt/zdsenv/gunicorn_config.py zds.wsgi
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    PrivateTmp=true

    [Install]
    WantedBy=multi-user.target


.. code:: text

    [Unit]
    Description=ZdS Gunicorn socket

    [Socket]
    #ListenStream=/run/gunicorn/socket
    ListenStream=/opt/zdsenv/bin/gunicorn.sock
    ListenStream=0.0.0.0:9000
    ListenStream=[::]:8000

    [Install]
    WantedBy=sockets.target

Configuration Solr
^^^^^^^^^^^^^^^^^^

La conf dans ``/etc/systemd/system/solr.service`` permet de lancer Solr à l'aide de ``systemctl start solr`` et l'arrêter avec ``systemctl stop solr``.

.. code:: text

    [Unit]
    Description=SolR ZdS
    After=syslog.target network.target remote-fs.target nss-lookup.target

    [Service]
    PIDFile=/run/solrzds/pid
    WorkingDirectory=/opt/zdsenv/apache-solr/example/
    ExecStart=/usr/bin/java -jar start.jar
    User=zds
    Group=zds
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s QUIT $MAINPID
    PrivateTmp=true

    [Install]
    WantedBy=multi-user.target

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

`Allez jeter un coup d'oeil à notre script de déploiement <https://github.com/zestedesavoir/zds-site/blob/dev/scripts/update_and_deploy.sh>` ! ;) (lequel appelle `le véritable script de déploiement <https://github.com/zestedesavoir/zds-site/blob/dev/scripts/deploy.sh>`).

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
            'bugtracker': u"https://github.com/zestedesavoir/zds-site/issues",
            'forum_feedback_users': u"/forums/communaute/bug-suggestions/",
            'contribute_link': u"https://github.com/zestedesavoir/zds-site/blob/dev/CONTRIBUTING.md",
            'short_description': u"",
            'long_description': u"Zeste de Savoir est un site de partage de connaissances "
                                u"sur lequel vous trouverez des tutoriels de tous niveaux, "
                                u"des articles et des forums d'entraide animés par et pour "
                                u"la communauté.",
            'association': {
                'name': u"Zeste de Savoir",
                'fee': u"20 €",
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
                    'provider_url': u"http://pdp.microjoe.org",
                },
                'licence_info_title': u'http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-lic'
                                      u'ences-sur-zeste-de-savoir/',
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
            'home_number': 4,
            'repo_path': os.path.join(BASE_DIR, 'articles-data')
        },
        'tutorial': {
            'repo_path': os.path.join(BASE_DIR, 'tutoriels-private'),
            'repo_public_path': os.path.join(BASE_DIR, 'tutoriels-public'),
            'default_license_pk': 7,
            'home_number': 5,
            'helps_per_page': 20,
            'content_per_page': 50,
            'feed_length': 5
        },
        'content': {
            'repo_private_path': os.path.join(BASE_DIR, 'contents-private'),
            'repo_public_path': os.path.join(BASE_DIR, 'contents-public'),
            'extra_contents_dirname': 'extra_contents',
            'max_tree_depth': 3,
            'default_license_pk': 7,
            'content_per_page': 50,
            'notes_per_page': 25,
            'helps_per_page': 20,
            'feed_length': 5,
            'user_page_number': 5,
            'default_image': os.path.join(BASE_DIR, "fixtures", "noir_black.png"),
            'import_image_prefix': 'archive',
            'build_pdf_when_published': True
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
            'home_number': 5,
            'old_post_limit_days': 90
        },
        'topic': {
            'home_number': 6,
        },
        'featured_resource': {
            'featured_per_page': 100,
            'home_number': 5,
        },
        'paginator': {
            'folding_limit': 4
        }
    }
