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

Issues #2718, #2658 et #2615
----------------------------

1. **Sauvegarder** le fichiers de configuration Nginx `zestedesavoir` et `zds-maintenance`.
2. Les **remplacer** par ceux [présents dans la documentation](http://docs.zestedesavoir.com/install/deploy-in-production.html).

Si le fichier `zds-maintenance` n'est pas dans la doc, c'est que vous n'êtes pas sur la bonne version.

Actions à faire pour mettre en prod la version : v15.7
======================================================

Issue #2401
-----------

La recherche est maintenant en français:

  - Arrêter Solr : `supervisorctl stop solr`
  - Regénérer le schema.xml : `python manage.py build_solr_schema > /votre/path/vers/solr-4.9.1/example/solr/collection1/conf/schema.xml`
  - Vérifier que les fichiers contractions_fr.txt et stopwords_fr.txt dans le dossier d'installation de Solr/example/solr/collection1/conf/lang/ sont pertinent.
  - Si les fichiers contractions_fr.txt et stopwords_fr.txt ne sont pas pertinent. Télécharger et remplacer les fichiers par ceux contenu dans [ce drive](https:// drive.google.com/folderview?id=0B5ux7uNoD6owfklUNnpOVWhuaTFkVjltSzR0UER2bWcwT1VQdUQ1WW5telU5TWFGLXFqM0U&usp=sharing).
  - Redémarrer Solr : `supervisorctl start solr`
  - Lancer l'indexation : `python manage.py rebuild_index`

Actions à faire pour mettre en prod la version : v15.9
======================================================

ZEP-12 aka Apocalypse
---------------------

![ZEP 12](http://i.ytimg.com/vi/UVFku_WzSc8/maxresdefault.jpg)

**Étapes préliminaires**

Il vous faut *absolument* faire une sauvegarde de secours de la base de données et du dossier `media/`.

Il est fortement conseillé de détecter les tutoriels et articles dont le dépot GIT est cassé via les commandes suivantes ([testées sur la bêta ici](https://github.com/artragis/zds-site/issues/238#issuecomment-131577950)) :

```bash
find tutoriels-private/ -mindepth 1 -maxdepth 1 -type d '!' -exec test -e '{}/.git/refs/heads/master' ';' -print
find articles-data/ -mindepth 1 -maxdepth 1 -type d '!' -exec test -e '{}/.git/refs/heads/master' ';' -print
```

et de les écarter temporairement (en les déplacant dans un autre dossier), afin de ne pas gêner la migration. Ils devront être ré-importé manuellement dans le futur, si cela est possible.

**Migrations des dépendences, de la base de données et des contenus**

- La recherche nécessite que les données dans la base soit encodées avec un charset "utf8_general_ci" mais tout type de charset utf8 semble correspondre.
  Pour vérifier que la base de données et les tables sont encodées avec un charset UTF-8, vous pouvez saisir la commande suivante (ne pas oublier de remplir le nom de la base de données dans le `WHERE`):
  ```sql
  SELECT T.table_name, CCSA.character_set_name FROM information_schema.`TABLES` T, information_schema.`COLLATION_CHARACTER_SET_APPLICABILITY` CCSA WHERE CCSA.collation_name = T.table_collation AND T.table_schema ="REMPLACER PAR LE NOM DE LA BASE DE DONNEES";
  ```
  Si dans la deuxième colonne, il apparait autre chose que le mot "utf8_general_ci", appliquez la commande suivante (remplacez les mots `dbname`, `dbusername` et `dbpassword` par respectivement le nom de la base, le nom de l'utilisateur qui a les droits de modifier la base et son mot de passe):
  ```bash
  DB="dbname";USER="dbusername";PASS="dbusername";mysql "$DB" --host=127.0.0.1 -e "SHOW TABLES" --batch --skip-column-names -u $USER -p=$PASS| xargs -I{} echo 'ALTER TABLE '{}' CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;'  | mysql "$DB" --host=127.0.0.1  -u $USER -p=$PASS
  ```
- La génération des PDFs par Pandoc, peut-être très longue, il est fortement conseillé de désactiver temporairement la génération de PDF. Pour cela, dans le fichier `settings_prod.py`, passer la variable `ZDS_APP['content']['build_pdf_when_published']` à `False`.  Il est nécessaire de relancer Django pour que ce paramètre soit pris en compte.
- Il faut maintenant migrer tous les contenus, pour cela utilisez la commande `python manage.py migrate_to_zep12`. Cette commande peut prendre plusieurs minutes.
- Lancez la génération des PDFs avec la commande : `python manage.py generate_pdf`, si vous désirez que les erreurs générées soient loggées, envoyez la sortie standard vers le fichier de votre choix. Prendre soin d'avoir activé le log de Pandoc.
- Repassez la variable `ZDS_APP['content']['build_pdf_when_published']` à `True`. Il est nécessaire de relancer Django pour que ce paramètre soit pris en compte.

**Migrations du module de recherche**

- Arrêter Solr : `systemctl stop solr` (remplacer `solr` par le nom exact du service)
- Regénérer `schema.xml` avec la commande `python manage.py build_solr_schema > /votre/path/vers/solr-4.9.1/example/solr/collection1/conf/schema.xml`
- Insérer les données pour la recherche dans la BDD : `python manage.py index_content`
- Changer la tâche cron qui permet d'indexer les contenus de `python manage.py update_index` à `python manage.py index_content --only-flagged >> /var/log/indexation.txt && python manage.py update_index >> /var/log/indexation.txt`
- Créer une autre tâche cron pour supprimer réguliérement le fichier de log `/var/log/indexation.txt`.
- Démarrer Solr : `systemctl start solr`
- Indexer le contenu avec Solr: `python manage.py rebuild_index`. Attention, cette commande peut prendre plusieurs minutes.

**Après la migration**

- Par défaut la pagination est mise à 42 éléments, mais nous affichons 2 ou 3 colonnes selon les largeurs d'écran. Pour la changer, il faut modifier la variable `ZDS_APP['content']['content_per_page']` dans `settings_prod.py`. Il est nécessaire de relancer Django pour que ce paramètre soit pris en compte.
- De nouvelles permissions ont été créées automatiquement par Django, il est nécessaire de les rajouter au groupe `staff`. Via l'interface d'administration, ajoutez au moins ces trois permissions :
    - `tutorialv2 | Contenu | Can change Contenu` (`tutorialv2.change_publishablecontent`) pour le droit au staff d'accéder et de modifier les contenus
    - `tutorialv2 | Validation | Can change Validation` (`tutorialv2.change_validation`) pour le droit au staff de valider des contenus
    - `tutorialv2 | note sur un contenu | Can change note sur un contenu` (`tutorialv2.change_contentreaction`) pour le droit au staff de modérer les commentaires sur les contenus



Actions à faire pour mettre en prod la version 14
=================================================

Forcer l'HTTPS pour les membres connectés - #1376
-------------------------------------------------

Dans le `settings_prod.py`, rajouter deux lignes :

```py
FORCE_HTTPS_FOR_MEMBERS = True
ENABLE_HTTPS_DECORATOR = True
```

Ajout d'un module de captcha - #1262
------------------------------------

Dans le fichier settings_prod.py, ajouter et paramètrer les lignes suivantes :

```py
USE_CAPTCHA = False
NOCAPTCHA = True  # Use the "No Captcha engine"
RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = 'la-cle-ici'
RECAPTCHA_PRIVATE_KEY = 'la-cle-ici'
```

(les clés d'applications sont à créer auprès de l'association)

Actions à faire pour mettre en prod la version 16
=================================================

Réparer la table HS
-------------------

**Avant déploiement :**

1. Se connecter au serveur MySQL : `mysql -u root -p`
2. Se mettre sur la base de ZdS : `use zdsdb;`
3. Regarder le contenu de la table oauth2_provider_accesstoken : `describe oauth2_provider_accesstoken;`
4. Si cette table contient une colonne nommée `skip_authorization`, la supprimer : `alter table oauth2_provider_accesstoken drop column skip_authorization;`
5. Quitter MySQL

Mise à jours de la version de Haystack à la 4.1
-----------------------------------------------

Pour mettre à jours la librairie, il vous faut lancer la commande `pip install --upgrade -r requirements.txt`


Indexation delta des forums
---------------------------

Mettre à jour la commande d'indexation, dans `/etc/systemd/system/zds-index-solr.service` :

```
ExecStart=/opt/zdsenv/bin/python /opt/zdsenv/ZesteDeSavoir/manage.py update_index
```

devient :


```
ExecStart=/opt/zdsenv/bin/python /opt/zdsenv/ZesteDeSavoir/manage.py update_index --remove --age=1
```

Changer la politique de génération des documents #3080
------------------------------------------------------

Mettre à jour le paramètre ZDS_APP["content"]["extra_content_generation_policy"] à "WATCHDOG".

Créer un service `systemd` dans `/etc/systemd/system/zds-watchdog.service` avec:

```
[Unit]
Description=Zeste de Savoir - Watchdog
After=network.target

[Service]
User=zds
Group=zds
WorkingDirectory=/opt/zdsenv/ZesteDeSavoir
ExecStart=/opt/zdsenv/bin/python /opt/zdsenv/ZesteDeSavoir/manage.py publication_watchdog
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

Activer puis lancer le service (en root):

```sh
systemctl enable zds-watchdog.service
systemctl start zds-watchdog.service
```

Il est possible de configurer le logging de ce module en surchargeant les logger `logging.getLogger("zds.pandoc-publicator")`, `logging.getLogger("zds.watchdog-publicator")`.

Repasser à l'ancienne version de `python-slugify` et sauver les contenus (#3383)
--------------------------------------------------------------------------------

1. Passer en maintenance ;
2. Mettre à jour les dépendances de zds afin de *downgrader* `python-slugify` : `pip install --upgrade -r requirements.txt` ;
3. Exécuter la commande suivante : `python manage.py adjust_slugs`. Noter les éventuels contenus pour lesquels cela ne fonctionnerai pas ;
4. Si pour certains contenus la commande échoue, il faut retrouver le dossier correspondant dans `/contents-private/` et donner à ce contenu le même slug ;
5. Quitter la maintenance.

Actions à faire pour mettre en prod la version 17
=================================================

CORS
----

Observer le fichier `/etc/nginx/conf.d/zds_headers.conf` et si une ligne au moins portant la mension `add_header Access-Control-Allow-Origin *;` existe (via, par exemple un `grep "add_header Access-Control-Allow-Origin" /etc/nginx/conf.d/zds_headers.conf`) supprimer toutes les lignes de cette forme.

Un redémarrage de nginx sera nécessaire en fin de procédure (`service nginx restart`).

TEMPLATE
--------

Vérifier qu'il n'y ait pas de variables `TEMPLATE_*` dans le `settings_prod.py`. Si c'est le cas les adapter en fonction du `settings.py` ou de [https://docs.djangoproject.com/en/1.9/ref/settings/#templates](https://docs.djangoproject.com/en/1.9/ref/settings/#templates).

REST_FRAMEWORK
--------------

Vérifier qu'on ne surcharge pas la variable `REST_FRAMEWORK` dans le `settings_prod.py`. Si c'est le cas l'adapter en fonction du `settings.py`.

MIGRATION
_________

1. Rendez-vous dans les migrations de l'app `django_app` de la dépendance `python-social-auth`:

~/.virtualenvs/zdsenv/lib/python2.7/site-packages/lib/python2.7/site-packages/social/apps/django_app/default/migrations/

2. Vérifiez qu'il n'y a que 3 fichiers de migration. S'il y en a plus, supprimez les migrations générées automatiquement (dispose du mot clé "auto" dans le nom).


Actions à faire pour mettre en prod la version 18
=================================================

Changements de configuration Nginx
----------------------------------

Une réécriture complète de la configuration Nginx a été faite en béta ; il faut donc refléter les changements en prod.

**Ces changements sont relativement lourds, donc une sauvegarde de `/etc/nginx` avant de faire quoi que ce soit n'est pas de trop. Ces changements doivent être fait *avant* la mise en prod, et tous les changements peuvent être fait sans aucun downtime, puisque l'ancienne configuration reste active tant que nginx n'est pas `reload`**

Créer un dossier `/opt/zdsenv/webroot`, et y symlink toutes les resources statiques:

```sh
mkdir /opt/zdsenv/webroot
cd /opt/zdsenv/webroot
ln -s ../ZesteDeSavoir/{static,media,errors,robots.txt} ./
```

**Aussi symlink toutes les autres resources qui doivent être accessibles, type les fichiers de vérification de Gandi/des Google Webmaster Tools**

Ensuite, le fichier `dhparam.pem` a été déplacé de `/etc/nginx/dhparam.pem` à `/etc/ssl/dhparam.pem`. Il faut donc le faire en prod (ou regénérer les dhparam via `openssl dhparam -out /etc/ssl/dhparam.pem 4096` ; cette commande peut prendre 2-3min)

Enfin, la localisation des certificats a été modifiée pour qu'elle soit la même en beta et en prod. En beta, les fichiers ont été symlink, il faut donc faire de même en prod (ou les déplacer/copier), en mettant la chaine de certificat dans `/etc/ssl/certs/zds-live.crt` et la clé dans `/etc/ssl/private/zds-live.key`. **Voir la configuration nginx actuelle pour voir de quel fichiers il s'agit.**

Une fois que ces changements sont fait, il faut copier la nouvelle configuration nginx dans `/etc/nginx`. Elle se trouve dans le dépot dans `doc/source/install/nginx/`.

Les anciens fichier dans `sites-{enabled,available}/` et dans `conf.d/` peuvent être virés s'il y en a ; les autres fichiers qui sont la "par défaut" doivent rester la (même si `mimes.types` semble être le seul fichier indispensable)

Symlink le fichier `zestedesavoir`: `ln -s ../sites-enabled/zestedesavoir /etc/nginx/sites-available/`

Enfin, **en prod uniquement**, symlink le fichier `prod-redirect`: `ln -s ../sites-enabled/prod-redirect /etc/nginx/sites-available/`

Tester la configuration avant de la recharger: (en root) `nginx -t`. S'il n'y a aucune erreur, recharger nginx via `systemctl reload nginx.service`

Notifications
-------------

1. Lors de l'application des migrations `python manage.py migrate`, Django va vous demander s'il doit supprimer la table topicfollowed. Renseignez oui.
2. Exécuter la commande `python manage.py migrate_subscriptions` pour migrer les anciennes notifications vers les nouvelles.

Si vous constatez des problèmes de performance, lancez la commande suivante : `mysqloptimize -uroot -p zdsdb`

Liste des tags exclus
---------------------

Dans le fichier settings.py, une nouvelle clé s'appelle top_tag_exclu (dans ZDS_APP -> forum -> top_tag_exclu), elle représente la liste des tags exclus des top tags. Vous pouvez ajouter des tags supplémentaire si la liste ne vous parait pas pertinente en surchargant
la clé dans le fichier de configuration de production.

ZEP-25
------

Il faut dans un premier temps supprimer les restes des tables des articles et tutoriels avant la ZEP-12 :

```sql
DROP TABLE article_article_subcategory;
DROP TABLE tutorial_tutorial_subcategory;
```

Avant de continuer il faut s'assurer d'avoir lancé les migrations. La commande `python manage.py migrate_to_zep25` permet de migrer automatiquement les contenus et de notifier les auteurs. Les logs sont très détaillés. **La commande peut être assez longue.** Pensez à modifier manuellement (via l'interface d'admin si besoin) les contenus publiés après la date spécifiés à la fin de la commande).

Les contenus non migrés automatiquement doivent l'être fait à la main, par les auteurs ou les validateurs. Seuls les contenus publiés sont migrés automatiquement.

Identifier les pk des votes pour la limite de désanonymisation - #1851
---------------------------------------------------------------------------

Lors de la migration, Django va éventuellement demander s'il faut supprimer les anciennes tables des votes. Il faut simplement répondre oui, dans ce cas.

La politique du site étant devenu de désanonymiser les votes +/-1 tout en gardant les anciens votes anonymes, il faut rechercher le PK du dernier vote afin de l'enregistrer dans le `settings_prod.py`. Voici la requète à executer pour obtenir ces informations (à faire après la migration) :

```sql
SELECT max(id) FROM utils_commentvote;
```

Le résultat de la requète doit être placé dans le paramètre `VOTES_ID_LIMIT` dans le fichier `settings_prod.py`. Dorénavant tout les nouveaux +/-1 ne seront plus anonymes.

Supprimer toute trace des tables pré-zep-12
-------------------------------------------

Il faudra supprimer en SQL:

- `SET FOREIGN_KEY_CHECKS=0;`
- `UPDATE tutorial_tutorial SET last_note_id=NULL;`
- `UPDATE article_article SET last_reaction_id=NULL;`
- `DROP TABLE tutorial_tutorial_subcategory;`
- `DROP TABLE tutorial_tutorial_authors;`
- `DROP TABLE tutorial_note;`
- `DROP TABLE tutorial_tutorialread;`
- `DROP TABLE tutorial_tutorial;`
- `DROP TABLE article_article_subcategory;`
- `DROP TABLE article_article_authors;`
- `DROP TABLE article_reaction;`
- `DROP TABLE article_articleread;`
- `DROP TABLE article_article;`
- `SET FOREIGN_KEY_CHECKS=1;`

S'il y a une erreur pour `article_article_subcategory` et `DROP TABLE tutorial_tutorial_subcategory;` c'est que les tables ont déjà été supprimées précédement (ZEP-25).

Actions à faire pour mettre en prod la version 18.2
===================================================

Notifications
-------------

### Supprime les notifications inutiles

Lancez la commande `python manage.py delete_useless_notif` pour supprimer toutes les notifications inutiles.

### Migre les souscriptions par e-mail

Lancez la commande `python manage.py migrate_email_subscription` pour migrer tous les sujets suivis par e-mail vers
les nouveaux modèles de souscriptions.

Actions à faire pour mettre en prod la version 19
=================================================

Page de contact
---------------

**À faire après la mise en production par une personne ayant les droits admin**.

Il faut ajouter les différents groupes de la page de contact via l'administration Django. Les informations pour les créer sont ci dessous : :

```
L'équipe de communication
    Email : communication@zestedesavoir.com
    Description :
    Responsable : ShigeruM
    groupe : Communication

L'association
    Email : zestedesavoir@gmail.com
    Description :
    Responsable : Kje
    groupe : bureau (à créer) ou CA (j'ai pas l'info au moment de la PR, voir avec Kje)

Le staff
    Email :
    Description :  Le staff est constitué de certains membres du site dont le but est de contrôler le contenu publié sur Zeste de Savoir. Ils sont en charge de la modération des messages sur les forums et commentaires, ainsi que de la validation et publication d'articles et/ou de tutoriels de Zeste de Savoir.
    Responsable : Thunderseb
    groupe : staffs

L'équipe technique
    Email :
    Description : L'équipe technique est constituée de certains membres du site dont le but est d'une part de s'assurer que le site reste toujours disponible en ligne, et d'autre part de corriger les bogues rencontrés sur le site ainsi que d'ajouter de nouvelles fonctionnalités. Des administrateurs systèmes, jusqu'aux designeurs, en passant par les développeurs back-end et intégrateurs front-end, ils s'occupent aussi de la maintenance du dépôt officiel du projet.
    Responsable : Andr0
    groupe : devs

```

Ces descriptions peuvent être modifiées via l'administration Django après la mise en production.

Actions à faire pour mettre en prod la version 20
=================================================

**(pré-migration)** Rendre unique les subscriptions
---------------------------------------------------

1. Lancer les 2 migrations suivantes :
  * `python manage.py migrate forum 0006_auto_20160720_2259`
  * `python manage.py migrate notification 0010_newpublicationsubscription`
1. Lancer la commande suivante :
  * `python manage.py uniquify_subscriptions >> mep_v20.log`
1. Jeter un oeil aux logs pour s'assurer que tout s'est bien passé.

**(pré-migration)** Nettoyer les tags existants
-----------------------------------------------

1. Lancer la commande `python manage.py clean_tags >> mep_v20.log`
1. Jeter un oeil aux logs pour s'assurer que tout s'est bien passé.

**(pré-migration)** Base de donnée
----------------------------------

(utilisateur `zds`)

1. Upgrade MySQL

    ```bash
    sudo aptitude update

    mkdir ~/mysql-5.5-backup
    sudo cp -r /etc/mysql ~/mysql-5.5-backup/etc_mysql

    mkdir ~/mysql-5.5-backup/database

    mysqldump --lock-all-tables -u zds -p --all-databases > ~/mysql-5.5-backup/database/dump.sql

    sudo apt-get remove mysql-server-5.5 mysql-server-core-5.5 mysql-client-5.5
    sudo apt-get autoremove

    # check that the innodb transactions files are gone (ibdata1, ib_logfile0 and ib_logfile1
    mkdir ~/mysql-5.5-backup/innodb
    sudo ls /var/lib/mysql/ | grep -e '^ib'
    # if they are still there, move them as root
    sudo sh -c 'mv /var/lib/mysql/ib* /home/zds/mysql-5.5-backup/innodb'
    sudo ls /var/lib/mysql/ | grep -e '^ib'
    # shouldn't show anything

    sudo aptitude -t jessie-backports install mysql-server mysql-client
    # if apt complains that mysql-server-5.6 wasn't configured, run the following:
    # sudo dpkg-reconfigure mysql-server-5.6
    # if there's a conflict because of mysql-client-5.5, accept the fix which suggests removing mysql-client-5.5

    sudo systemctl restart mysql

    # create missing innodb tables
    mysql -u zds -p mysql <  ./scripts/migrations/20160718_01_mysql-5.6-innodb-tables.sql

    sudo systemctl restart mysql

    mysql -u zds -p < ~/mysql-5.5-backup/database/dump.sql
    ```

1. Modifier le fichier `/etc/mysql/my.cnf`, ajouter la ligne suivante dans la section `[mysqld]`, près des autres configs innodb:

    ```diff
    # * InnoDB
    #
    # InnoDB is enabled by default with a 10MB datafile in /var/lib/mysql/.
    # Read the manual for more InnoDB related options. There are many!
    #
    +innodb_file_per_table=on
    +innodb_file_format=barracuda
    +innodb_large_prefix=on
    ```

1. Relancer les services

    ```bash
    sudo systemctl restart mysql
    sudo systemctl restart zds.{service,socket}
    sudo systemctl restart solr
    sudo systemctl restart zds-index-solr.service
    # this one takes ages
    ```

1. (sans sudo,) lancer le script de migration: `./scripts/migrations/20160718_02_utf8mb4.sh`
1. En cas d'erreur MySQL dans le script, le script va s'arrêter pour qu'on corrige les erreurs. Relancer le script ne pose aucun problème, il peut tourner autant de fois que nécessaire jusqu'à ce qu'il termine avec succès une fois toutes les erreurs corrigées.
1. Ajouter la bonne option à `settings_prod.py` :

    ```diff
    DATABASES = {
        'default': {
    [...]
            'CONN_MAX_AGE': 600,
    +       'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
    ```

1. Modifier le `/etc/mysql/my.cnf` pour que les sections correspondantes contiennent bien les infos suivantes :

    ```
    [client]
    default-character-set=utf8mb4

    [mysql]
    default-character-set=utf8mb4

    [mysqld]
    character-set-client-handshake=false
    character-set-server=utf8mb4
    collation-server=utf8mb4_unicode_ci
    ```

1. Relancer MySQL

    `sudo systemctl restart mysql`

Issue 3620
----------

Dans le `settings_prod.py` : ajouter `ZDS_APP['site']['secure_url'] = 'https://zestedesavoir.com'`

Issue 3762
----------

1. Après avoir lancé les migrations, lancer la commande :

    1. `python manage.py fix_persistent_notifications >> mep_v20.log`
    1. Jeter un oeil aux logs pour s'assurer que tout s'est bien passé.

(Ne pas oublier de lancer les migrations en terminant cette MEP !)

HTTP/2
------

Installer une version plus récente de nginx qui supporte HTTP/2 et vérifier la configuration de nginx :

```
sudo apt-get update && apt-get -t jessie-backports install nginx openssl
sudo nginx -t
```

Pour chaque fichier dans `/etc/nginx/sites-enabled/`, remplacer spdy par http2:

```diff
-        listen 443 ssl spdy default_server;
-        listen [::]:443 ssl spdy default_server;
+        listen 443 ssl http2 default_server;
+        listen [::]:443 ssl http2 default_server;
```

Relancer nginx : `sudo service nginx restart``

Vérifier que zds fonctionne comme il faut en HTTP et HTTPS.

Polices pour les exports de contenus
------------------------------------

Utilisateur `zds`:

1. `cp -r export-assets/fonts/* ~/.fonts/truetype`
1. `fc-cache -f -v > update-fonts-cache.log`
1. Vérifier dans les logs que les nouvelles polices ont été chargées.
1. Mettre à jour `settings_prod.py` :

    ```diff
    -                    "-V mainfont=Merriweather -V monofont=\"Andale Mono\" "
    +                    "-V mainfont=Merriweather -V monofont=\"SourceCodePro-Regular\" "
    ```

Actions à faire pour activer le thème d'Halloween
=================================================

Ajouter `ZDS_APP['visual_changes'] = ['clem-halloween']` à `settings_prod.py`.

---

**Notes auxquelles penser lors de l'édition de ce fichier (à laisser en bas) :**

Le déploiement doit être autonome. Ce qui implique que :

1. La mise à jour de dépendances est automatique et systématique,
2. La personne qui déploie ne doit pas réfléchir (parce que c'est source d'erreur),
3. La personne qui déploie ne doit pas avoir connaissance de ce qui est déployé (techniquement et fonctionnellement).


Actions à faire pour l'upgrade v21
==================================

**(pré-migration)** Supprimer les notifications persistantes
------------------------------------------------------------

1. Lancer la commande suivante :
  * `python manage.py fix_persistent_notifications >> ~/mep_v21.log`
1. Jeter un oeil aux logs pour s'assurer que tout s'est bien passé.

Actions à faire pour masquer la barre de recherche
--------------------------------------------------

Ajouter `ZDS_APP['display_search_bar'] = False` à `settings_prod.py`

`settings_prod.py`
------------------

```diff
      'zds.utils.ThreadLocals',
      'zds.middlewares.SetLastVisitMiddleware.SetLastVisitMiddleware',
      'zds.middlewares.profile.ProfileMiddleware',
-     'zds.middlewares.ForceHttpsMembersMiddleware.ForceHttpsMembersMiddleware',
  )
```

A propos du logging:
--------------------

Mettre à jour le `settings_prod.py` en suivant `doc/source/install/configs/settings_prod.py`.


Actions faites sur la prod avant la v22
=======================================

Mettre à jour nginx
-------------------

* Supprimer `/etc/apt/sources.list.d/nginx.list`
* `apt update`
* `systemctl stop nginx`
* `apt remove 'nginx-*'`
* `apt-get -t jessie-backports install nginx-full`
    - `N or O  : keep your currently-installed version`
    - `rm /etc/nginx/sites-available/default`
    - `dpkg --configure -a`
* `systemctl restart nginx`

Actions à faire pour l'upgrade v22
==================================

Issue #2743
-----------

Lancer la commande de calcul du nombre de caractères des contenus publiés : `python manage.py adjust_char_count`.

Maj de Raven + releases
-----------------------

Mettre à jour le `settings_prod.py` :

```diff
+from raven import Client
+from zds.utils.context_processor import get_git_version
```

```diff
# https://docs.getsentry.com/hosted/clients/python/integrations/django/
RAVEN_CONFIG = {
  'dsn': 'to-fill',
+ 'release': get_git_version()['name'],
}
```

```diff
       'sentry': {
            'level': 'ERROR',  # For beta purpose it can be lowered to WARNING
            'class': 'raven.handlers.logging.SentryHandler',
+           'dsn': RAVEN_CONFIG['dsn'],
        },
```

Elasticsearch (PR #4096)
------------------------

Pour installer Elasticsearch, les commandes suivantes sont à effectuer (en *root*):

+ S'assurer que `jessie-backports` est disponible dans `/etc/apt/sources.list`
+ S'assurer que Java 8 est disponible par défaut: `java -version`, sinon l'installer :
    * `apt-get update && apt-get install openjdk-8-jdk`.
    * Une fois installé, passer de Java 7 à Java 8 en le sélectionnant grâce à `update-alternatives --config java`.
+ Installer Elasticsearch ([informations issues de la documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html)):
    * Ajouter la clé publique du dépôt : `wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -`
    * Installer apt-transport-https `apt-get install apt-transport-https`
    * Ajouter le dépôt pour Elasticsearch 5 : `echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-5.x.list`
    * Installer Elasticsearch 5 : `apt-get update && apt-get install elasticsearch`
+ Configurer la mémoire utilisée par Elastisearch:
    Remplacer les options `-Xms2g` et `-Xmx2g` par

    ```
    -Xms512m
    -Xmx512m
    ```

    Dans `/etc/elasticsearch/jvm.options` (**Peut évoluer dans le futur**).
+ Lancer Elasticsearch:

    ```bash
    systemctl daemon-reload
    systemctl enable elasticsearch.service
    systemctl start elasticsearch.service
    ```

+ Vérifier que le port 9200 n'est pas accessible de l'extérieur (sinon, configurer le firewall en conséquence)
+ Ajouter [ce plugin](https://github.com/y-ken/munin-plugin-elasticsearch) à Munin:

    * Installer la dépendance manquante:

        ```bash
        apt install libjson-perl
        ```
    * Suivre les instructions du [README.md](https://github.com/y-ken/munin-plugin-elasticsearch/blob/master/README.md)
    * Penser à enlever le(s) plugin(s) Solr et relancer `munin-node`

Une fois Elasticsearch configuré et lancé,

+ Passer à 3 *shards* ([conseillé par Firm1](https://github.com/zestedesavoir/zds-site/pull/4096#issuecomment-269861811)): `ES_SEARCH_INDEX['shards'] = 3` dans `settings_prod.py`.
+ Indexer les données (**ça peut être long**):

    ```
    python manage.py es_manager index_all
    ```

Une fois que tout est indexé,

+ Repasser `ZDS_APP['display_search_bar'] = True` dans `settings_prod.py`.

+ Configurer *systemd*:

    * `zds-es-index.service` :

        ```
        [Unit]
        Description=Reindex SOLR Service

        [Service]
        Type=oneshot
        User=zds
        Group=zds
        ExecStart=/opt/zds/zdsenv/bin/python /opt/zds/zds-site/manage.py es_manager index_flagged
        ```

    * `zds-es-index.timer`:

        ```
        [Unit]
        Description=ES reindex flagged contents

        [Timer]
        OnCalendar=*:30:00
        Persistent=true

        [Install]
        WantedBy=timers.target
        ```

    * Supprimer Solr et ajouter Elasticsearch:

        ```bash
        systemctl stop zds-index-solr.timer
        systemctl disable zds-index-solr.timer

        systemctl enable zds-es-index.timer
        systemctl start zds-es-index.timer
        ```

+ Désinstaller Solr :
    * `pip uninstall pysolr django-haystack`

+ Supprimer Solr
    * `rm -rf /opt/zds/solr-*`

+ Supprimer les tables devenues inutiles dans MySQL:

    * `mysql -u zds -p -B zdsdb`

    ```sql
    DROP TABLE search_searchindexextract;
    DROP TABLE search_searchindexcontainer;
    DROP TABLE search_searchindexcontent_authors;
    DROP TABLE search_searchindexcontent_tags;
    DROP TABLE search_searchindextag;
    DROP TABLE search_searchindexauthors;
    DROP TABLE search_searchindexcontent;
    ```

Actions à faire pour mettre en prod la version : v23
====================================================

Tribunes
--------

+ Ajouter à la fin de `/etc/munin/plugin-conf.d/zds.conf`

```
    [zds_total_tribunes]
    env.url https://zestedesavoir.com/munin/total_opinions/
    env.graph_category zds
```

+ Créer le symlink nécessaire dans `/etc/munin/plugins` (`ln -s /usr/share/munin/plugins/django.py zds_total_tribunes`)

+ Réindexer les données (un champ a été rajouté):

    ```
    python manage.py es_manager index_all
    ```

A propos de social auth:
------------------------

Ne pas oublier de mettre le middleware `'zds.member.utils.ZDSCustomizeSocialAuthExceptionMiddleware'`.

Forcer le paramètre `SOCIAL_AUTH_RAISE_EXCEPTIONS = False`.


Mise à jour d'ElasticSearch
---------------------------

1. `sudo apt update`
2. `sudo apt upgrade elasticsearch`
2. `systemctl restart elasticsearch.service`


Actions à faire pour mettre en prod la version : v24
====================================================

Ticket #4313
------------

+ Via l'admin Django, ajouter la permission `member.change_bannedemailprovider` aux groupes autorisés à gérer les fournisseurs e-mail bannis.

Actions à faire pour mettre en prod la version : v25
====================================================

Avant le déploiement:
---------------------

Node.js, yarn et npm
--------------------

En root: Installer node 8 et Yarn:

```
curl -sL https://deb.nodesource.com/setup_8.x | bash -
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
apt-get update && apt-get install build-essential nodejs yarn
```

Mise à jour d'ElasticSearch (#420)
----------------------------------

```
sudo apt update
sudo apt upgrade elasticsearch # Ne pas remplacer jvm.options
systemctl restart elasticsearch.service
```

Mise à jour des settings
------------------------

* Dans les `settings*.py`, renommer `sec_per_minute` en `characters_per_minute` si présent
* Dans les `settings*.py`, renommer `litteral_name` en `literal_name`

Smileys Clem (#4408)
--------------------

+ Ajouter `ZDS_APP['member']['old_smileys_allowed'] = True` au `settings_prod.py`.
+ Télécharger le fichier [`clem_smileys.conf`](https://raw.githubusercontent.com/zestedesavoir/zds-site/f11a1346c80741046fc02c5a9e68e001da3e4c6b/doc/source/install/configs/nginx/snippets/clem_smileys.conf) dans `/etc/nginx/snippets/`.
+ Éditer `/etc/nginx/sites-available/zestedesavoir` et ajouter `include snippets/clem_smileys.conf;` dans le bloc `location ~* ^/(static|media|errors)/ {`
+ Tester la configuration : `nginx -t`


Lancer le script de déploiement
-------------------------------

Casquettes
----------

Par défaut, les casquettes ne sont modifiables que par les super-utilisateurs. Pour autoriser un groupe à le faire, il faut lui ajouter la permission `utils.change_hat` via l'admin Django.

Il faut ensuite créer des casquettes. Une commande est disponible pour ajouter une casquette à tous les membres d'un groupe. Lancez donc les commandes suivantes :

1. Activer le venv

```
python manage.py add_hat_to_group 'CA' "Conseil d'Administration"
python manage.py add_hat_to_group 'devs' 'Équipe technique'
python manage.py add_hat_to_group 'staffs' 'Staff'
python manage.py add_hat_to_group 'Communication' 'Communication'
python manage.py add_hat_to_group 'dtc' 'DTC'
```

Menu au survol (#4454)
----------------------

Les menus s’ouvrent désormais au survol lorsque l’option est activée. Étant donné que cette option est activée par défaut, désactiver cette option pour tous les utilisateurs existants via le shell de Django afin de ne pas troubler la communauté :

1. Toujours dans le venv, `python manage.py shell`

```python
from zds.member.models import Profile
Profile.objects.update(is_hover_enabled=False)
```

Responsables de groupe (#4600)
------------------------------

Il faut réassigner les responsables de chaque groupe dans l'admin django post-déploiement.


Versions supérieures à la v25
=============================

Ce fichier n'est plus utilisé après la v25. Il a été remplacé par un *changelog* disponible sur le [wiki GitHub](https://github.com/zestedesavoir/zds-site/wiki).
