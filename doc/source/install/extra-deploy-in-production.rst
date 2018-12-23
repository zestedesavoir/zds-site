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
| IPv4           | ``176.31.187.88``           | ``92.243.26.160``           |
+----------------+-----------------------------+-----------------------------+
| IPv6           | x                           | Pas encore disponible…      |
+----------------+-----------------------------+-----------------------------+
| Identifiant    | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+
| Mot de passe   | *Demande privée*            | *Demande privée*            |
+----------------+-----------------------------+-----------------------------+

Premier déploiement
===================

Toute la procédure suppose un déploiement dans ``/opt/zds``.

Utilisateur local
-----------------

Zeste de Savoir tourne sous l'utilisateur **zds** et le groupe **root**.

Installation des outils
-----------------------

-  python
-  virtualenv (dans /opt/zds/zdsenv/)
-  git

Clone du repo et configuration de prod
--------------------------------------

.. code:: bash

    cd /opt/ && mkdir zds && chown zds:zds -R zds
    su zds

    cd /opt/zds
    mkdir -p data/tutoriels-private data/tutoriels-private data/tutoriels-public data/articles-data
    git clone https://github.com/zestedesavoir/zds-site.git

    cd zds-site
    make install-debian

    cd /opt/zds
    pip install --user virtualenv # Ajout du module virtualenv
    virtualenv zdsenv --python=python2 # Création du répertoire "zdsenv"

    cd zds-site
    vim zds/settings_prod.py


Dans ``settings_prod.py``, remplacez toutes les valeurs ``to-fill``:

.. literalinclude:: configs/settings_prod.py
  :language: python
  :caption: :download:`configs/settings_prod.py`

Il est possible de personnaliser ZdS pour n'importe quel site communautaire de
partage. Un ensemble de paramètres est disponible dans le fichier
``settings.py`` via le dictionnaire ``ZDS_APP``. Vous pourrez donc écraser ces
variables par défaut dans votre fichier ``settings_prod.py``, comme illustré
dans le fichier ci-dessus.

Installation de l'application de base
-------------------------------------

Suivre `l'installation sous Linux <linux-install.html>`_ en tenant compte des subtilités suivantes :

-  Installer `les outils front <frontend-install.html>`__ n'est pas nécessaire, le front étant packagé par Travis.
- `Installez Elasticsearch <extra-install-es.html>`_ ;
- `Installez LaTeX <extra-install-latex.html>`_.
-  Installer MySQL5.6 depuis backports: ``sudo apt -t jessie-backports install mysql-server mysql-client libmysqlclient-dev``
-  Installer les dépendances de production avec ``pip install --upgrade -r requirements-prod.txt``

Outils spécifiques à un serveur de run
--------------------------------------

Gunicorn
~~~~~~~~

.. literalinclude:: configs/gunicorn_config.py
  :language: python
  :caption: :download:`configs/gunicorn_config.py`

Nginx
~~~~~

Installer nginx.

Une version récente de nginx est nécessaire pour utiliser HTTP/2. Si la version installée est inférieure à la version 1.9.5 il faut la mettre à jour avec celle `des dépot nginx <https://nginx.org/en/linux_packages.html#stable>`__. Toutefois, HTTP/2 n'est pas nécessaire au bon fonctionnement de Zeste de Savoir, pensez juste à adapter ``sites-available/zestedesavoir``.

La configuration nginx de Zeste de Savoir est séparée en plusieurs fichiers, en plus des quelques fichiers de configuration par défaut de nginx:

.. code:: text

    /etc/nginx
    |- nginx.conf # Fichier de configuration principal
    |- sites-available/
    |  |- prod-redirect # Redirection de www.zestedesavoir.com -> zestedesavoir.com en prod
    |  \- zestedesavoir # Configuration propre au site
    \- snippets/ # Dossier contenant des configurations incluses dans différents fichiers
       |- antispam.conf # Incluse dans zestedesavoir
       |- headers.conf # Headers type HSTS, CSP (et X-Robots-Tags sur la beta)
       |- ssl.conf # Définition des protocoles SSL à utiliser + conf. des certificats
       |- gzip.conf # Configuration pour la compression
       |- proxy.conf # Headers à passer au proxy (gunicorn)
       \- static-cache.conf # Headers à rajouter pour les contenus statiques (cache)


.. literalinclude:: configs/nginx/nginx.conf
  :language: nginx
  :caption: :download:`configs/nginx/nginx.conf`

.. literalinclude:: configs/nginx/sites-available/prod-redirect
  :language: nginx
  :caption: :download:`configs/nginx/sites-available/prod-redirect`

.. literalinclude:: configs/nginx/sites-available/zestedesavoir
  :language: nginx
  :caption: :download:`configs/nginx/sites-available/zestedesavoir`

.. literalinclude:: configs/nginx/snippets/antispam.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/antispam.conf`

.. literalinclude:: configs/nginx/snippets/gzip.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/gzip.conf`

.. literalinclude:: configs/nginx/snippets/headers.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/headers.conf`

.. literalinclude:: configs/nginx/snippets/proxy.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/proxy.conf`

.. literalinclude:: configs/nginx/snippets/ssl.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/ssl.conf`

.. literalinclude:: configs/nginx/snippets/static-cache.conf
  :language: nginx
  :caption: :download:`configs/nginx/snippets/static-cache.conf`


TLS : Let's Encrypt
~~~~~~~~~~~~~~~~~~~

Le site est servi en https avec un certificat Let's Encrypt install avec
`certbot <https://certbot.eff.org>`_.

- Installer ``certbot``:
    - ``sudo apt-get install certbot -t jessie-backports``
- Générer le nécessaire:
    - ``certbot certonly --webroot -w /opt/zds/zdsenv/webroot -d zestedesavoir.com -d www.zestedesavoir.com``
- Mettre un cron pour régénérer les certificats, avec l'utilisateur root:
    - ``23 */2 * * * certbot renew --quiet --post-hook "service nginx reload"``

Solr
~~~~

`Voir la documentation de Solr <install-solr.html>`_.

MySQL
~~~~~

Zeste de Savoir nécessite MySQL 5.6. Voici la configuration de production :

.. literalinclude:: configs/my.cnf
  :language: mysql
  :caption: :download:`configs/my.cnf`

.. literalinclude:: configs/conf.d/my.cnf
  :language: mysql
  :caption: :download:`configs/conf.d/my.cnf`

.. literalinclude:: configs/conf.d/mysqldump.cnf
  :language: mysql
  :caption: :download:`configs/conf.d/mysqldump.cnf`

.. literalinclude:: configs/conf.d/mysql.cnf
  :language: mysql
  :caption: :download:`configs/conf.d/mysql.cnf`

.. literalinclude:: configs/conf.d/mysqld_safe_syslog.cnf
  :language: mysql
  :caption: :download:`configs/conf.d/mysqld_safe_syslog.cnf`



Supervisor
~~~~~~~~~~

Installer supervisor.

Créer deux configurations :

Configuration ZdS
^^^^^^^^^^^^^^^^^

Les confs dans ``/etc/systemd/system/zds.service`` et ``/etc/systemd/system/zds.socket``
permettent de lancer le serveur applicatif de Zeste de Savoir (Gunicorn) à l'aide
de ``systemctl start zds.{service,socket}`` et l'arrêter avec ``systemctl stop zds.{service,socket}``.

``zds.service`` nécessite la création manuelle de ``/run/gunicorn`` appartenant à ``zds`` : ``sudo mkdir /run/gunicorn && sudo chown zds /run/gunicorn``.

.. literalinclude:: configs/zds.service
  :language: bash
  :caption: :download:`configs/zds.service`

.. literalinclude:: configs/zds.socket
  :language: bash
  :caption: :download:`configs/zds.socket`

Configuration Solr
^^^^^^^^^^^^^^^^^^

La conf dans ``/etc/systemd/system/solr.service`` permet de lancer Solr à l'aide
de ``systemctl start solr`` et l'arrêter avec ``systemctl stop solr``.

.. literalinclude:: configs/solr.service
  :language: bash
  :caption: :download:`configs/solr.service`

Munin
~~~~~

Configuration générale
^^^^^^^^^^^^^^^^^^^^^^

Installer le noeud Munin : ``apt-get install munin-node``.

On obtient les suggestions de plugins à installer avec ``munin-node-configure --suggest`` et les commandes à lancer pour les activer via ``munin-node-configure --shell``.

Pour l'instant le serveur de graphe est fourni par SpaceFox et `est visible ici <http://munin.kisai.info>`__. Seul SpaceFox peut mettre à jour cette configuration. Le serveur de graphe accède au serveur en SSH avec cette clé publique, placée dans le home de l'utilisateur munin (sous debian, l'utilisateur créé par le packet munin a son home dans ``/var/lib/munin``, donc sa clé doit être dans ``/var/lib/munin/.ssh/authorized_keys``) :

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
    ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/zds_total_tribunes

Créer le fichier ``/etc/munin/plugin-conf.d/zds.conf`` et y ajouter la config des graphes
propres à ZdS :

.. literalinclude:: configs/munin/zds.conf
  :caption: :download:`configs/munin/zds.conf`

Mise à jour d'une instance existante
====================================

`Allez jeter un coup d'oeil à notre script de déploiement <https://github.com/zestedesavoir/zds-site/blob/dev/scripts/update_and_deploy.sh>`_ ! ;) (lequel appelle `le véritable script de déploiement <https://github.com/zestedesavoir/zds-site/blob/dev/scripts/deploy.sh>`_).
