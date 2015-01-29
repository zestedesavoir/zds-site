===
API
===

Informations générales
======================

En-têtes possibles
------------------

- ``Accept`` : L'API accepte plusieurs rendus, à savoir le ``JSON`` (par défaut) et l'``XML``. Toutes les requêtes peuvent donc renvoyer un résultat dans ces deux formats.
- ``Content-Type`` : L'API accepte plusieurs parsers, à savoir le ``JSON`` (par défaut), l'``XML``, le formulaire et le multi part (``x-www-form-urlencoded``).
- ``Authorization`` : Renseigne le token d'authentification pour toutes les requêtes qui nécessitent une authentification.

Les caches
----------

- Cache : Toutes les requêtes ```GET`` disposent d'un cache de 15 minutes (paramétrable).
- ``ETag`` : Pour toutes les requêtes ``GET`` et ``PUT``, un ``ETag`` est calculé par le serveur et renvoyé dans l'en-tête de la réponse (disponible sous le même nom, ``ETag``).

L'avantage dans l'utilisation d'un ``ETag`` se situe principalement dans la possibilité d'alléger le back-office dans sa charge de travail. Il ne sera pas toujours nécessaire d'aller chercher l'information s'il remarque qu'elle n'a pas été modifiée entre deux requêtes.

Voici le fonctionnement d'un ETag :

- Lorsqu'un client fait appel à l'API, la réponse inclue un ``ETag`` avec une valeur correspondant à un hash de la donnée retournée par l'API. La valeur de cette ``ETag`` est sauvegardée pour une prochaine utilisation si nécessaire.
- Au prochain même appel du client sur l'API, le client peut inclure dans le header de sa requête, l'attribut ``If-None-Match`` avec le précédent ``ETag`` renvoyé par le back-office.
- Si l'``ETag`` n'a pas changé, le code de la réponse sera ``304 - Not Modified`` et aucune donnée ne sera renvoyée.
- Si l'``ETAg`` a changé, le back-office fera la requête et renverra la donnée avec un nouveau ``ETag``. Ce nouveau ``ETag`` sera sauvegardé et utilisé pour de prochaines requêtes.

Toutes les informations concernant la mise en oeuvre de ces systèmes de cache sont disponibles dans la documentation `DRF-extensions <http://chibisov.github.io/drf-extensions/docs/>`_.

Authentification
----------------

L'authentification est du type OAuth2 (dont la spécification du protocole est disponible via `ce lien <http://tools.ietf.org/html/rfc6749>`_).

Son fonctionnement est le suivant :

- Chaque client de l'API s'inscrit en tant qu'application tierce en faisant une requête auprès d'un administrateur puisqu'une page d'inscription n'existe pas encore.
- A la fin de l'inscription, le système devra renvoyer une ``ZDS_AUTH_KEY`` et une ``ZDS_AUTH_SECRET`` au développeur.
- Lorsqu'un membre veut se logguer au site via un client externe, le client devra donc envoyer à l'API :
    - le login : login de l'utilisateur sur le site.
    - le password : mot de passe de l'utilisateur sur le site.
    - le ``ZDS_AUTH_KEY`` : identifiant du client de l'API.
    - le ``ZDS_AUTH_SECRET`` : clé secrète du client de l'API.
- Un token doit être généré qui signifie "le membre x veut se connecter à l'API via le client y".

L'authentification se base sur l'utilisation d'access token et de refresh token :

.. sourcecode:: json

    {
    "access_token": "<your-access-token>",
    "scope": "read",
    "expires_in": 86399,
    "refresh_token": "<your-refresh-token>"
    }

1. L'utilisateur se log pour la première fois grâce à un client à l'API.
2. Le serveur lui renvoi son access token avec son expiration et son refresh token sans expiration.
3. Durant la session, l'access token est utilisé dans les requêtes.
4. A chaque fois que l'access token expire, le client refait une authentification avec le refresh token et la clé secrète.

Django REST Swagger
===================

Django REST Swagger est une bibliothèque qui génère automatiquement la documentation d'une API Django basé sur la bibliothèque Django REST framework.

Cette documentation est accessible par l'url ``http://www.zestedesavoir.com/api/`` et, via cette page, il est possible de :

- Lister toutes les APIs pour toutes les ressources.
- Connaitre les paramètres, les codes d'erreur et un exemple de réponse.
- Exécuter toutes les routes disponibles dans l'API.

Pour maintenir cette documentation, rendez-vous sur `sa documentation <http://django-rest-swagger.readthedocs.org/en/latest/>`_ qui explique sur quoi se base la bibliothèque pour générer la documentation et comment y rajouter de l'information.