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

