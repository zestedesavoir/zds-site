===
API
===

Informations générales
======================

Version courante
----------------

L'API est toujours en développement et n'est pas encore versionnée. Même si elle le deviendra une fois son développement stabilisé, elle doit être vue comme une bêta avec les changements que cela peut impliquer dans ses paramètres et ses réponses.

Schéma
------

L'API est accessible à partir du domaine ``zestedesavoir.com/api/`` (prochainement ``api.zestedesavoir.com``) et en HTTP ou en HTTPS. Dès lors que vous effectuez des requêtes authentifiées le HTTPS devient obligatoire. De base, toutes les réponses sont renvoyées en JSON.

.. sourcecode:: bash

    $ curl -i https://zestedesavoir.com/api/membres/

    HTTP/1.1 200 OK
    Server: nginx
    Date: Sat, 14 Feb 2015 19:41:29 GMT
    Content-Type: application/json
    Transfer-Encoding: chunked
    Connection: keep-alive
    Vary: Accept-Encoding
    ETag: "d8f9437e4f88b4e6e2ad0a6d770d970bfdd5bbbc689cc3b3390759d06d4f105a"
    Vary: Accept, Cookie
    Allow: GET, POST, HEAD, OPTIONS
    P3P: CP="ALL DSP COR PSAa PSDa OUR NOR ONL UNI COM NAV"

    {
      "count":0,
      "next":null,
      "previous":null,
      "results":[]
    }

Tous les timestamp sont retournés au le format ISO 8601 : ``YYYY-MM-DDTHH:MM:SSZ``.

Les verbes HTTP
---------------

- ``GET`` : Utilisés pour récupérer des ressources.
- ``POST`` : Utilisés pour créer des ressources.
- ``PUT`` : Utilisés pour mettre à jour des ressources.
- ``DELETE`` : Utilisés pour supprimer des ressources.

Les autres verbes ne sont pas supportés.


Les formats d'entrées/sorties
-----------------------------

Par défaut, le serveur renvoie les réponses au format ``JSON`` mais il gère aussi le ``XML``. Pour demander au serveur de renvoyer les réponses en ``XML``, il faut utiliser l'en-tête ``Accept`` en spécifiant ``application/xml`` comme valeur (``application/json`` pour recevoir du ``JSON``).

.. sourcecode:: bash

    $ curl -H "Accept: application/xml" https://zestedesavoir.com/api/membres/

Les `formats de sortie (en) <http://www.django-rest-framework.org/api-guide/renderers/>`_ sont renseignés dans le fichier ``settings.py`` sous l'attribut ``DEFAULT_RENDERER_CLASSES`` du dictionnaire ``REST_FRAMEWORK``. Pour Django Rest Framework, tous les formats de sorties sont des ``renderer``.

.. sourcecode:: python

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.XMLRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
    }

Plusieurs formats d'entrées sont supportés par le serveur, à savoir le ``JSON`` (par défaut), l'``XML``, le formulaire et le multi part (``x-www-form-urlencoded``). Ces formats peuvent être renseignées avec l'en-tête ``Content-Type``.

.. sourcecode:: bash

    $ curl -H "Content-Type: application/xml" https://zestedesavoir.com/api/membres/

Les `formats d'entrée (en) <http://www.django-rest-framework.org/api-guide/parsers/>`_ sont renseignés dans le fichier ``settings.py`` sous l'attribut ``DEFAULT_PARSER_CLASSES`` du dictionnaire ``REST_FRAMEWORK``. Pour Django Rest Framework, tous les formats d'entrée sont des ``parser``.

.. sourcecode:: python

    REST_FRAMEWORK = {
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.JSONParser',
            'rest_framework.parsers.XMLParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser',
        ),
    }

Cache
-----

Un cache spécifique à l'API est mis en place pour mettre en cache toutes les méthodes ``GET``. Le système n'est pas spécifique à Django Rest Framework mais est disponible via une librairie tierce qui a été développée spécialement pour fonctionner avec DRF, `DRF-Extensions (en) <http://chibisov.github.io/drf-extensions/docs/>`_.

Pour placer un cache, il suffit d'annoter la méthode ``GET`` voulue avec l'annotation ``@cache_response()`` (comme le mentionne la `documentation à ce sujet (en) <http://chibisov.github.io/drf-extensions/docs/#caching>`_
). Par exemple, la méthode ``GET`` pour récupérer la liste paginée des membres ressemblerait au code ci-dessous.

.. sourcecode:: python

    class MemberListAPI(ListCreateAPIView, ProfileCreate, TokenGenerator):
        queryset = Profile.objects.all()
        list_key_func = PagingSearchListKeyConstructor()

        @cache_response(key_func=list_key_func)
        def get(self, request, *args, **kwargs):
            return self.list(request, *args, **kwargs)

Dans le contexte de Zeste de Savoir, ce n'est pas suffisant. Comme la plupart des routes ``GET`` peuvent prendre des paramètres, il faut permettre au cache de distinguer une URL X avec des paramètres et une URL Y avec d'autres paramètres. Ceci se fait en spécifiant une clé au cache de la méthode. Par exemple, pour la pagination, si aucune clé n'est renseignée, le cache renverra toujours le même résultat peu importe la page souhaitée.

Pour enrichir la clé d'un cache, DRF-Extensions propose les ``KeyConstructor``. Toutes les informations et les possibilités à ce sujet sont disponibles dans la `documentation de cette librairie (en) <http://chibisov.github.io/drf-extensions/docs/#key-constructor>`_.

ETag
----

Un ETag est un identifiant unique assigné par le serveur à chaque version d'une ressource accessible via une URL. Si la ressource accessible via cette URL change, un nouvel ETag sera assigné. Lorsque le client utilise cet en-tête, cela permet d'alléger le serveur : il suffit au serveur de comparer l'ETag de la ressource et celui fourni par le client pour décider si une requête en base de données est nécessaire.

Le calcul de l'ETag n'est pas natif à Django Rest Framework mais est accessible via la `bibliothèque DRF-Extensions (en) <http://chibisov.github.io/drf-extensions/docs/#conditional-requests>`_. Le calcul est ajouté sur toutes les méthodes ``GET`` et ``PUT``. Il est inutile de calculer des ETags pour des requêtes ``POST`` et ``DELETE`` puisque ces deux méthodes ont pour objectif de créer et supprimer des ressources.

Pour placer un ETag, il suffit d'annoter la méthode voulue avec l'annotation ``@etag()``. Par exemple, la méthode ``GET`` pour récupérer la liste paginée des membres ressemblerait au code ci-dessous.

.. sourcecode:: python

    class MemberListAPI(ListCreateAPIView, ProfileCreate, TokenGenerator):
        queryset = Profile.objects.all()
        list_key_func = PagingSearchListKeyConstructor()

        @etag(key_func=list_key_func)
        def get(self, request, *args, **kwargs):
            return self.list(request, *args, **kwargs)

Dans le contexte de Zeste de Savoir, ce n'est pas suffisant. Comme la plupart des routes ``GET`` et ``PUT`` peuvent prendre des paramètres, il faut permettre au cache de distinguer une URL X avec des paramètres et une URL Y avec d'autres paramètres. Ceci se fait en spécifiant une clé à l'ETag de la méthode. Par exemple, pour la pagination, si aucune clé n'est renseignée, l'ETag ne sera jamais recalculé peu importe la page souhaitée.

Pour enrichir la clé de l'ETag, DRF-Extensions propose les ``KeyConstructor``. Toutes les informations et les possibilités à ce sujet sont disponibles dans la `documentation de cette librairie (en) <http://chibisov.github.io/drf-extensions/docs/#key-constructor>`_.

**Note :** L'ETag et le cache peuvent fonctionner ensemble. Une méthode peut être annotée avec ``@etag()`` et ``@cache_response()``.

Pour utiliser un ETag, faites une requête vers n'importe quelle ressource en ``GET`` ou ``PUT``. Dans les en-têtes de la réponse figurera l'ETag et sa valeur. Pour les prochaines requêtes vers cette même ressource, renseignez l'en-tête ``If-None-Match`` avec l'ETag sauvegardé comme valeur.

.. sourcecode:: bash

    $ curl -H "If-None-Match: da54a5d285fbfc52bf62637147ecb5c11c7199ed78848b7f43781df0cd039b89" https://zestedesavoir.com/api/membres/

Si le serveur constate qu'il n'y a aucun changement dans la ressource, il renverra une réponse ``304 Not Modified`` avec un corps vide. Il n'est alors pas nécessaire de mettre à jour les valeurs sauvegardées en locale pour les ressources désirées. Dans le cas contraire, les ressources demandées seront renvoyées avec un nouvel ETag à sauvegarder.

Throttling
----------

Le `throttling` permet d'imposer des limites au nombre de requêtes possibles pour un utilisateur anonyme et connecté. Cette fonctionnalité est native à Django Rest Framework et se met en place facilement via le fichier ``settings.py`` du projet sous l'attribut ``DEFAULT_THROTTLE_CLASSES`` du dictionnaire ``REST_FRAMEWORK`` pour spécifier les types de throttling à appliquer et sous ``DEFAULT_THROTTLE_RATES`` pour spécifier les taux.

.. sourcecode:: python

    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle'
        ),
        'DEFAULT_THROTTLE_RATES': {
            'anon': '60/hour',
            'user': '2000/hour'
        }
    }

Il existe d'autres configurations possibles. Pour en prendre conscience, rendez-vous dans la `documentation du throttling (en) <http://www.django-rest-framework.org/api-guide/throttling/>`_.

Pagination
----------

La pagination permet d'éviter au serveur de faire des requêtes trop lourdes sur la base de données. Par exemple, si un client désire récupérer la liste de tous les utilisateurs de la plateforme et que cette même plateforme dispose d'un très grand nombre d'utilisateurs, la requête en base de données pourrait être lourde. Coupler à ceci des intentions malveillantes pour faire tomber le serveur, paginer les listes de ressources est presque une mesure de sécurité.

La pagination peut être configurée directement dans les vues de l'API mais aussi dans le fichier ``settings.py`` pour s'appliquer à l'ensemble des listes des ressources de l'API. Dans le fichier ``settings.py``, ``PAGINATE_BY`` renseigne la taille d'une page, ``PAGINATE_BY_PARAM`` permet aux clients de modifier la taille d'une page et ``MAX_PAGINATE_BY`` permet d'imposer une taille maximale.

.. sourcecode:: python

    REST_FRAMEWORK = {
        'PAGINATE_BY': 10,                  # Default to 10
        'PAGINATE_BY_PARAM': 'page_size',   # Allow client to override, using `?page_size=xxx`.
        'MAX_PAGINATE_BY': 100,             # Maximum limit allowed when using `?page_size=xxx`.
    }

Toutes les informations complémentaires à ce sujet sont disponibles dans la `documentation de la pagination (en) <http://www.django-rest-framework.org/api-guide/pagination/>`_.

Son utilisation est simple, il suffit de renseigner la page avec le paramètre ``page`` et, optionnellement, ``page_size`` pour renseigner la taille de la page. Par exemple, récupérer la page 2 d'une page de taille 3 ressemblera à la requête suivante.

.. sourcecode:: bash

    $ curl https://zestedesavoir.com/api/membres/?page=2&page_size=3

Dans la réponse, on retrouve des méta informations à propos de la liste : la taille totale de la liste, l'URL vers les pages suivantes et précédentes et la liste attendue avec la ressource souhaitée.

.. sourcecode:: json

    {
        "count": 43,
        "next": "https://zestedesavoir.com/api/membres/?page=3&page_size=2",
        "previous": "https://zestedesavoir.com/api/membres/?page=1&page_size=2",
        "results": [
            {
                "pk": 41,
                "username": "boo123451234",
                "is_active": false,
                "date_joined": "2015-02-08T15:53:12.666839"
            },
            {
                "pk": 40,
                "username": "boo12345123",
                "is_active": false,
                "date_joined": "2015-02-08T15:53:09.436657"
            }
        ]
    }

Authentification
================

Bibliothèque tierce choisie
---------------------------

Django Rest Framework supporte plusieurs systèmes d'authentification (comme en témoigne la `documentation sur l'authentification (en) <http://www.django-rest-framework.org/api-guide/authentication/>`_). Sur Zeste de Savoir, il a été décidé d'utiliser OAuth2 (dont la spécification du protocole est disponible via `ce lien (en) <http://tools.ietf.org/html/rfc6749>`_) pour tenter d'avoir le système le plus sécurisé possible.

L'authentification n'est pas directement dans Django Rest Framework, il ne fait que supporter des librairies tierces qui s'en occupent. La librairie choisie est `Django OAuth Toolkit <https://django-oauth-toolkit.readthedocs.org/en/0.7.0/>`_ pour sa forte compatibilité avec Django Rest Framework, sa maintenance et sa compatibilité Python 3 et Django 1.7 (ou plus).

Toute sa configuration est détaillée dans la `documentation de cette bibliothèque <https://django-oauth-toolkit.readthedocs.org/en/0.7.0/rest-framework/getting_started.html>`_.

Utilisation
-----------

Créer un client
^^^^^^^^^^^^^^^

Des requêtes authentifiées ne peuvent se faire sans un client. Ce client est appelé "Application" dans Django OAuth Toolkit. C'est pourquoi il sera nommé ainsi dans la suite de cette documentation. Pour créer une application, il faut en demander la création auprès des administrateurs de la plateforme. Ils seront en mesure d'en créer 2 types : confidentielle et publique. Une application confidentielle permet l'utilisation d'un ``refresh_token`` au contraire d'une application publique qui se contente d'envoyer un ``access_token``.

Dans l'interface d'administration de Django, se rendre dans la section "OAuth2_provider" puis créer une application. Un identifiant et une clé secrète cliente seront automatiquement générés et seront les informations à communiquer auprès des développeurs tiers. Il est ensuite nécessaire de renseigner au minimum la personne concernée par la demande, le type du client et le `grant type`.

- Utilisateurs concernés : Cela ne veut pas dire que ces utilisateurs sont les seuls à pouvoir s'authentifier avec l'application. Cela les rend juste responsables en cas de dérive.
- Type du client : Privilégiez le type confidentiel au public pour permettre aux clients tiers de ne pas redemander aux utilisateurs leurs informations de connexion après l'expiration de leur token.
- `grant type` : Renseignez `Resource owner password-based` pour baser l'authentification sur le mot de passe du compte utilisateur sur la plateforme.

.. note::

    Si vous `chargez les fixtures <./utils/fixture_loaders.html>`_, un tel client, lié à l'utilisateur ``admin``, est déjà créé, avec les identifiants suivants:

    - ``client_id``: ``w14aIFqE7z90ti1rXE8hCRMRUOPBP4rXpfLZIKmT`` ;
    - ``client_secret``: ``0q4ee800NWs8cSHa0FIbkTLwEncMqYHOCAxNkt9zRmd10bRk1J18TkbviO5QHy2b66ggzyLADm79tJw5BQf2XfApPnk0nogcFaYhtNO33uNlzzT8sXfxu3zzBFu5Wejv``.


Récupérer les tokens d'authentification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pour récupérer les tokens, les développeurs doivent exécuter une requête en ``POST`` et en spécifiant l'identifiant et la clé secrète de l'application, le `grant type` spécifié dans l'application et le pseudo/mot de passe du compte utilisateur qui souhaite s'authentifier. Une requête basique ressemblerait à la commande ci-dessous. Toute fois, sachez que les caractères spéciaux doivent être échappés dans une commande ``curl`` comme celle exposé dans cette documentation. On ne peut que vous conseiller d'exécuter cette même requête plutôt dans une console REST comme il en existe des centaines.

.. sourcecode:: bash

    $ curl -X POST -H "Content-Type: application/json" -d '{
            "username": "YOUR_USERNAME",
            "password": "YOUR_PASSWORD",
            "grant_type": "password",
            "client_id": "CLIENT_ID",
            "client_secret": "CLIENT_SECRET"
        }' https://zestedesavoir.com/oauth2/token/

Si l'application est bien en "confidentiel", la réponse à cette requête exposera 2 tokens, son type, sa date d'expiration et sa portée.

- ``access_token`` : Token a utiliser dans les requêtes que vous souhaitez authentifier.
- ``token_type`` : Le type de l'OAuth2 sera toujours `Bearer` et devra être spécifié dans les prochaines requêtes.
- ``expires_in`` : Le `timestamp` correspondant à la date d'expiration de l'``access_token``.
- ``refresh_token`` : Permet d'effectuer une nouveau requête pour récupérer les tokens d'authentification sans spécifier le pseudo et le mot de passe utilisateur.
- ``scope`` : Portée du token d'authentification générée pour le serveur.

.. sourcecode:: json

    {
        "access_token": "wERPXXHpYAsJV29eATLjSO2u5bamyw",
        "token_type": "Bearer",
        "expires_in": 36000,
        "refresh_token": "1HJaUfFYA5jE54e2Wz1yEMRi89z6er",
        "scope": "read write"
    }

**Note :** S'il existe déjà un token actif pour l'utilisateur final, l'ancien token sera invalidé au profit du nouveau.

Utiliser un access_token
^^^^^^^^^^^^^^^^^^^^^^^^

Pour utiliser l'``access_token``, il faut le renseigner dans l'en-tête de la requête sous l'attribut ``Authorization`` avec comme valeur ``Bearer wERPXXHpYAsJV29eATLjSO2u5bamyw``.

.. sourcecode:: bash

    $ curl -H "Authorization: Bearer wERPXXHpYAsJV29eATLjSO2u5bamyw" https://zestedesavoir.com/api/membres/1/

**Attention :** La requête doit se faire en HTTPS obligatoirement.

Utiliser un refresh_token
^^^^^^^^^^^^^^^^^^^^^^^^^

Si le token n'est plus valide ou que vous avez perdu l'``access_token`` de l'utilisateur final, il faut en récupérer un nouveau grâce au ``refresh_token``. Son utilisation est similaire à l'authentification sauf qu'il n'est pas nécessaire de renseigner le pseudo et le mot de passe mais le ``refresh_token`` à la place et de spécifier un ``grant_type`` avec comme valeur ``refresh_token``.

.. sourcecode:: bash

    $ curl -X POST -H "Content-Type: application/json" -d '{
            "grant_type": "refresh_token",
            "client_id": "CLIENT_ID",
            "client_secret": "CLIENT_SECRET",
            "refresh_token": "YOUR_REFRESH_TOKEN"
        }' https://zestedesavoir.com/oauth2/token/

A la suite de cela, de nouveaux tokens seront renvoyés et devront être sauvegardés pour une prochaine utilisation si nécessaire.

Documentation (utilisation)
============================

Django REST Swagger est une bibliothèque qui génère automatiquement la documentation d'une API Django basée sur la bibliothèque Django REST framework.

Cette documentation est accessible par l'url ``http://zestedesavoir.com/api/`` et, via cette page, il est possible de :

- Lister toutes les APIs pour toutes les ressources.
- Connaitre les paramètres, les codes d'erreur et un exemple de réponse.
- Exécuter toutes les routes disponibles dans l'API.

Pour maintenir cette documentation, rendez-vous sur `sa documentation (en) <http://django-rest-swagger.readthedocs.org/en/latest/>`_ qui explique sur quoi se base la bibliothèque pour générer la documentation et comment y rajouter de l'information.
