Ce fichier liste les actions à faire pour mettre en production les différentes
versions de Zeste de Savoir.

Ajoutez tout simplement vos instructions à la suite de ce fichier.

Actions à faire pour mettre en prod la version : v1.2
=====================================================

Issue #1520
-----------

Dans le `settings_prod.py`

- Remplacer `SITE_URL = 'http://zestedesavoir.com'` par `ZDS_APP['site']['url'] = 'http://zestedesavoir.com'`
- Remplacer `ANONYMOUS_USER = "anonyme"` par `ZDS_APP['member']['anonymous_account'] = 'anonyme'`
- Remplacer `EXTERNAL_USER = "Auteur externe"` par `ZDS_APP['member']['external_account'] = 'Auteur externe'`
- Remplacer `BOT_ACCOUNT = 'Clem'` par `ZDS_APP['member']['bot_account'] = 'Clem'`
- Remplacer `BETA_FORUM_ID = x` par `ZDS_APP['forum']['beta_forum_id'] = x`

Issue #1341
-----------

Installer les outils d'optimisation :

```bash
apt-get install optipng
apt-get install jpegoptim
```

Mettre à jour le fichier `settings_prod.py` :

```python
THUMBNAIL_OPTIMIZE_COMMAND = {
'png': '/usr/bin/optipng {filename}',
 'gif': '/usr/bin/optipng {filename}',
'jpeg': '/usr/bin/jpegoptim {filename}'
}
```


Actions à faire pour mettre en prod la version : v1.3
=====================================================

Actions à faire pour mettre en prod la version : v1.4
=====================================================

Issue #381
----------

1. Pour un compte **facebook** :
  - allez sur https://developers.facebook.com/apps/?action=create et cliquer sur "Create New App" en vert
  - Dans les paramètre de l'application crée cliquez sur “Add Platform”. Dans les options fournies, choisissez Web, et remplissez l'url du site avec "http://zestedesavoir.com" (adaptez l'adresse en fonction de l'adresse sur laquelle vous déployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_FACEBOOK_KEY = "clé"`
et `SOCIAL_AUTH_FACEBOOK_SECRET = "secret"` obtenu via l'application facebook

2. Pour un compte **twitter** :
  - allez sur https://apps.twitter.com/app/new et creez une nouvelle application
  - remplissez les informations, et dans votre url de callback pensez à renseigner `http://zestedesavoir.com/complete/twitter/` (adaptez l'adresse en fonction de l'adresse sur laquelle vous déployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_TWITTER_KEY = "clé"`
et `SOCIAL_AUTH_TWITTER_SECRET = "secret"`  obtenu via l'application twitter

3. Pour un compte **google plus** :
  - allez sur https://console.developers.google.com/ et creez une nouvelle application
  - remplissez les informations, et dans votre url de callback pensez à renseigner `http://zestedesavoir.com/complete/google-oauth2/` (adaptez l'adrese en fonction de l'adresse sur laquelle vous testez déployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "clé"` et `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "secret"`  obtenu via l'application google

Issue #1487
-----------

Définir des positions pour les catégories de tutoriels dans la partie admin du site (par défaut toutes à 0). L'odre d'affichage se fait par ordre croissant. Les sous-catégories sont triées automatiquement par ordre alphabétique.

ZEP-3
-----

#### Schéma

Mettre à jour le modèle de données.
```
python manage.py migrate
```

Si un souci apparait via South qui grogne avec un message comme celui-ci pas de panique !
```
Inconsistent migration history
The following options are available:
    --merge: will just attempt the migration ignoring any potential dependency
        conflicts.
```
Il suffit de lui obéir et tout devrait rentrer dans l'ordre
```
python manage.py migrate --merge
```

#### Données

Pour la ZEP, il faut aussi générer les "aides" de base : rédacteur, correcteur, repreneur, illustrateur.
Tout est déjà prêt dans les fixtures dédiées à cela :
```
python load_factory_data.py fixtures/advanced/aide_tuto_media.yaml
```

Actions à faire pour mettre en prod la version : v1.5
=====================================================

Issue #1541
-----------

Désormais les utilisateurs anonyme et auteur externe doit faire partie du groupe "bot".

Il faudra donc :

1. créer le groupe "bot"
2. vérifier que `settings.ZDS_APP['member']['bot_group']` vaut bien `"bot"`
3. Aller dans l'interface de promotion des utilisateurs pour ajouter les comptes auteur externe et anonyme au groupe bot

npm
---

Lancer la commande `npm -v` et voir le résultat. Si le résultat est 1.x.x, lancer la commande `sudo npm install -g npm`.

Faire pointer nginx sur `static/` au lieu de `dist/`.

Actions à faire pour mettre en prod la version : v1.6
=====================================================

Issue #1724
-----------

Rajouter cette ligne dans le fichier `zds/settings_prod.py` pour versionner les fichier statiques :

```python
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.CachedStaticFilesStorage"
```


Actions à faire pour mettre en prod la version : v1.7
=====================================================

Issue #2058
-----------

Rajouter ces lignes dans le `settings_prod.py` :

```python
ZDS_APP['site']['googleAnalyticsID'] = 'UA-27730868-1'
ZDS_APP['site']['googleTagManagerID'] = 'GTM-WH7642'
```


Vérifier que `EMAIL_BACKEND` est bien définit dans le `settings_prod.py` car il a maintenant une valeur par défaut. La configuration par défaut sur la prod devrait être `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'`.

Actions à faire pour mettre en prod la version : v1.8
=====================================================

Issue #1455 Django 1.7
----------------------

**Avant** de lancer la migration de la base, prévenir Django que `easy_thumbnail` est déjà OK :


```
python manage.py migrate --fake easy_thumbnails
```

Le reste l'est aussi mais Django est incapable de le détecter tout seul pour cette app.

**Attention** : il est possible que Django perde l'information du "migrate fake" pendant la migration et donc plante sur cette étape pendant le déploiement. Si c'est le cas, pas de panique, il suffit de releancer les migrations à la main et de redémarrer l'application :

```
cd /opt/zdsenv/ZesteDeSavoir/
source ../bin/activate
python manage.py migrate --fake easy_thumbnails
python manage.py migrate
deactivate
sudo supervisorctl restart zds
```

Désinstaller south: `pip uninstall south`. La MAJ de Django de la 1.6 à la 1.7 sera faite par le script (via la mise à jour des _requirements_).

Déploiement de Django 1.7
-------------------------

_(A priori spécifique à zestedesavoir.com, mais ça peut aider selon l'installation qui est faite du site)_

1. Le fichier `unicorn_start` est inutile et peut être supprimé.
2. La conf `gunicorn_config.py` peut être pas mal simplifiée. Fichier utilisé en **bêta**, quelques adaptations peuvent être nécessaires pour la production :

```python
command = '/opt/zdsenv/bin/gunicorn'
pythonpath = '/opt/zdsenv/ZesteDeSavoir'
bind = 'unix:/opt/zdsenv/bin/gunicorn.sock'
workers = 7
user = 'zds'
group = 'zds'
errorlog = '/opt/zdsenv/logs/gunicorn_error.log'
loglevel = 'info'

```

3. Mettre à jour la configuration supervisor pour utiliser la bonne manière de lancer Gunicorn. Fichier utilisé en **bêta**, quelques adaptations peuvent être nécessaires pour la production :

```
[program:zds]
directory = /opt/zdsenv/
command = /opt/zdsenv/bin/gunicorn -c /opt/zdsenv/gunicorn_config.py zds.wsgi
stdout_logfile = /opt/zdsenv/logs/supervisor_stdout.log
stderr_logfile = /opt/zdsenv/logs/supervisor_stderr.log

```

4. Redémarrer Supervisor pour prendre en compte les modifications : `sudo service supervisor restart`


Issue #1634
-----------

Exécuter la commande suivante : `sudo apt-get install libffi-dev`


Actions à faire pour mettre en prod la version : v15.6
======================================================

Issue #1511, Issue #983 et Pull Request #2766
---------------------------------------------

Fix sur la recherche d'article avec Solr :

  - Arrêter Solr : `supervisorctl stop solr`
  - Mettre à jour solr et employer la version 4.9.1 (`wget http://archive.apache.org/dist/lucene/solr/4.9.1/solr-4.9.1.zip` dans le dossier ou doit se trouver Solr, probablement `/opt/zdsenv/ZesteDeSavoir/`)
  - Regénérer le schema.xml : `python manage.py build_solr_schema > /votre/path/vers/solr-4.9.1/example/solr/collection1/conf/schema.xml`
  - Redémarrer Solr : `supervisorctl start solr`
  - Lancer l'indexation : `python manage.py rebuild_index`

Issue #2753 et #2751
--------------------

Règle le souci de migration de oauth2_provider.
La mise à jour de oauth2_provider met la table oauth2_provider dans un état bancale à cause d'une migration non appliquée par South (vu que non utilisé par Django 1.7).
Pour régler ça, il faut faire les modifications de la migration nous-même.

  - Se connecter sur mysql : `mysql -u <user> -D <base> -p` (puis entrer le mot de passe au prompt)
  - Ajouter une colonne à la table oauth2_provider_application : `ALTER TABLE oauth2_provider_application ADD COLUMN skip_authorization TINYINT NOT NULL DEFAULT 0;`
  - Ajouter une clé étrangère à la table oauth2_provider_accesstoken : `ALTER TABLE oauth2_provider_accesstoken ADD CONSTRAINT fk_user_oauth2_provider_accesstoken FOREIGN KEY(user_id) REFERENCES auth_user(id);`
  - Les deux commandes doivent passer sans souci
  - Quitter mysql
  - Puis feinter la migration de oauth2_provider : `python manage.py migrate oauth2_provider --fake`

Ajout d'un groupe com'
----------------------

*À faire une fois la migration effectuée avec un super-utilisateur*

Permet aux membres responsables de la communication de pouvoir ajouter/supprimer des Unes et la phrase "Nouveau"

  - Dans la page d'administration
  - Créer un groupe "Communication"
  - Attribuer les droits `perms.featured.change_featuredresource` à ce nouveau groupe
  - Ajouter les membres responsables de la communication à ce groupe
