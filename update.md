Ce fichier liste les actions � faire pour mettre en production les diff�rentes
versions de Zeste de Savoir.

Ajoutez tout simplement vos instructions � la suite de ce fichier.

Actions � faire pour mettre en prod la version : v1.2
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

Mettre � jour le fichier `settings_prod.py` :

```python
THUMBNAIL_OPTIMIZE_COMMAND = { 
'png': '/usr/bin/optipng {filename}',
 'gif': '/usr/bin/optipng {filename}', 
'jpeg': '/usr/bin/jpegoptim {filename}' 
}
```


Actions � faire pour mettre en prod la version : v1.3
=====================================================

Actions � faire pour mettre en prod la version : v1.4
=====================================================

Issue #381
----------

1. Pour un compte **facebook** : 
  - allez sur https://developers.facebook.com/apps/?action=create et cliquer sur "Create New App" en vert
  - Dans les param�tre de l'application cr�e cliquez sur � Add Platform �. Dans les options fournies, choisissez Web, et remplissez l'url du site avec "http://zestedesavoir.com" (adaptez l'adresse en fonction de l'adresse sur laquelle vous d�ployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_FACEBOOK_KEY = "cl�"`
et `SOCIAL_AUTH_FACEBOOK_SECRET = "secret"` obtenu via l'application facebook

2. Pour un compte **twitter** : 
  - allez sur https://apps.twitter.com/app/new et creez une nouvelle application
  - remplissez les informations, et dans votre url de callback pensez � renseigner `http://zestedesavoir.com/complete/twitter/` (adaptez l'adresse en fonction de l'adresse sur laquelle vous d�ployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_TWITTER_KEY = "cl�"`
et `SOCIAL_AUTH_TWITTER_SECRET = "secret"`  obtenu via l'application twitter

3. Pour un compte **google plus** : 
  - allez sur https://console.developers.google.com/ et creez une nouvelle application
  - remplissez les informations, et dans votre url de callback pensez � renseigner `http://zestedesavoir.com/complete/google-oauth2/` (adaptez l'adrese en fonction de l'adresse sur laquelle vous testez d�ployez)
  - dans votre fichier `settings_prod.py` rajouter les variables `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "cl�"` et `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "secret"`  obtenu via l'application google

PR #1785
--------

V�rifier que `EMAIL_BACKEND` est bien d�finit dans le `settings_prod.py` car il a maintenant une valeur par d�faut. La configuration par d�faut sur la prod devrait �tre `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'`.
