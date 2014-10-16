# Configuration des serveurs

Zeste de Savoir est installe en 1 tiers (sur un seul serveur donc).

## Paramètres généraux

Paramètre | Valeur
---|---
OS | Linux, Debian 7 "Wheezy"
Serveurs web | Nginx
Moteur WSGI | Gunicorn
SGBD | MySQL
Contrôle des process | Supervisor
Surveillance | Munin

## Paramètres spécifiques
 | Pré-prod | Prod
---|---|---
Nom | preprod.zestedesavoir.com | zestedesavoir.com
IPv4 | `178.32.53.245` | -
IPv6 | `176.31.187.88` | `2001:41d0:52:100::b4f`
Login | _Demande privée_ | _Demande privée_
Mot de passe | _Demande privée_ | _Demande privée_

# Premier déploiement

Toute la procédure suppose un dépoiement dans `/opt/zdsenv`.

## Installation des outils

- python, 
- virtualenv (dans /opt/zdsenv/), 
- git

## Clone du repo et configuration de prod

- `git clone https://github.com/zestedesavoir/zds-site.git`
- `mkdir tutoriels-private`
- `mkdir tutoriels-public`
- `mkdir articles-data`
- `touch zds/settings_prod.py`
- `vim zds/settings_prod.py`

On édite le fichier de manière à rajouter les infos spécifiques au serveur courant. Par exemple :
```text
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
```

## Installation de l'application de base

Suivre [l'installation complète sous Linux](install-linux.md) en tenant compte des subtilités suivantes :

- Installer [les outils front](gulp.md) (l'installation rapide suffit)
- Ne pas lancer le serveur à la fin de l'étape _"Lancer ZdS"_
- Installer toutes les dépendances requises à l'étape _"Aller plus loin"_

## Outils spécifiques à un serveur de run

### Utilisateur local

Zeste de Savoir tourne sous l'utilisateur **zds** et le groupe **root**.

### Gunicorn

Installer Gunicorn dans le virtualenv.

Dans `/opt/zdsenv/unicorn_start` :

```shell
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
```

### Nginx

Installer nginx. Sous Debian, la configuration est splittée par site. Pour Zeste de Savoir elle se fait dans `/etc/nginx/sites-available/zestedesavoir` :

```text
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

    location /author-files/ {
        index index.html index.php;
        alias /home/zds/tutos_sdzv3/script/;
        include php.fast.conf;
    }

    location /roundcube/{
        index index.html index.php;
        alias /opt/roundcube/;
        #autoindex on;
        include php.fast.conf;
    }

    location = /robots.txt {
        alias /opt/zdsenv/ZesteDeSavoir/robots.txt ;
    }

    location /static/admin/ {
        alias /opt/zdsenv/lib/python2.7/site-packages/django/contrib/admin/static/admin/;
    }

    location /stats/ {
        alias /opt/zdsenv/stats/;
    }

    location /static/ {
        alias /opt/zdsenv/ZesteDeSavoir/dist/;
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

    location /teasing/ {
           #### proxy_pass http://176.31.187.88:8001/teasing/;
            proxy_set_header X-Forwarded-Host $server_name;
            proxy_set_header X-Forwaded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header REMOTE_ADDR $remote_addr;
            add_header P3P 'CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"';
            proxy_pass http://zdsappserver/teasing/;


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
```

### Solr

**???**

### Supervisor

Installer supervisor.

Créer deux configurations :

#### Configuration ZdS

La conf dans `/etc/supervisor/conf.d/zds.conf` permet de lancer Solr à l'aide de `supervisorctl start zds` et l'arrêter avec `supervisorctl stop zds`.

```text
[program:zds]
command = /opt/zdsenv/unicorn_start ;
user = zds ;
stdout_logfile = /opt/zdsenv/logs/gunicorn_supervisor.log ;
redirect_stderr = true ;
```

#### Configuration Solr

La conf dans `/etc/supervisor/conf.d/solr.conf` permet de lancer Solr à l'aide de `supervisorctl start solr` et l'arrêter avec `supervisorctl stop solr`.

```text
[program:solr]
directory=/opt/zdsenv/ZesteDeSavoir/apache-solr/example
command=java -jar start.jar
autostart=true
autorestart=true
stderr_logfile=/opt/zdsenv/logs/solr.err.log
stdout_logfile=/opt/zdsenv/logs/solr.out.log
```

### Munin

#### Configuration générale

Installer le noeud Munin : `apt-get install munin-node`.

On obtient les suggestions de plugins à installer avec `munin-node-configure --suggest` et les commandes à lancer pour les activer via `munin-node-configure --shell`.

Pour l'instant le serveur de graphe est fourni par SpaceFox et [est visible ici](http://munin.kisai.info). Seul SpaceFox peut mettre à jour cette configuration. Le serveur de graphe accède au serveur en SSH avec cette clé publique :

```text
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBsfYaz5d4wtyTM0Xx1TjpJt0LuZ2Il9JZD2+s4hNQToNBaqT3aafG1SuHuQkqjvIQrI28NEkjALQIp4zD7BOeeW9QlAwE7uiebi3FcwLfaPFwq5qvnpyOSmbktCjHX24a14ozgDPY5diPkOsyMdEYz/KTybSvFvgUjzUSCLBQ2EWj0CBktY6cFC45pvVCsdd/ToDsEVbhixyNmlOMc+FB/oT8CC6ZoDezSXQGaO51/zLS8l4ieBIcB4tK3JdJI+fFv5FJsfgMK+DbNV4pikw9qEZJlASQCU69L+YR7MxTXNCqRyQ1Z4qxH4ZdPELmNOoMB8dHxxBX7TGP+Hvpm3AH munin@Yog-Sothoth
```

#### Configuration spécifique à ZdS

Créer les liens vers le plugin Django-Munin :

```shell
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
```

Ajouter les métriques suivantes au fichier `/etc/munin/plugin-conf.d/munin-node` :

```text
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
```

# Mise à jour d'une instance existante

```
cd /opt/zdsenv
source bin/activate
cd ZesteDeSavoir
```

## Arrêt de l'application

`sudo supervisorctl stop zds`

## Mise à jour de l'application

Mise à jour du code : 

`git pull`

Migration de la BDD :

`python manage.py migrate`

MAJ des statics :

Sous le compte **zds** :

```
source /usr/local/nvm/nvm.sh
gulp clean
gulp build
```

Modification du `settings_prod.py` :

Si un utilisateur anonyme et un utilisateur permettant de récupérer les tutoriels venant de l'extérieur
existent déjà, configurez les constantes `ANONYMOUS_USER` et `EXTERNAL_USER` pour que ces dernières
aient pour valeur le pseudo desdits utilisateurs.

Sinon, utilisez au choix le shell django ou bien

```
python manage.py loaddata fixtures/users.py #crée aussi un utilisateur admin, staff et user, donc utilisez cette commande avec précaution.
```


Réindexation Solr :

`python manage.py rebuild_index`

## Redémarrage de l'application

`sudo supervisorctl start zds`

