==========================
Arborescence du *back-end*
==========================

Le *back-end* est divisé en différents modules qui assurent chacun une tâche du site. Ceux-ci sont intégralement localisés dans le dossier ``zds/``.

Arborescence générale de ``zds/``
=================================

On retrouve un dossier pour chaque module du site :

.. sourcecode:: bash

    zds/
    ├── article/ # module des articles
    │   └── ...
    ├── featured/ # module des mises en avant
    │   └── ...
    ├── forum/ # module des forums
    │   └── ...
    ├── gallery/ # module des galleries
    │   └── ...
    ├── member/ # module des membres
    │   └── ...
    ├── mp/ # module des messages privés
    │   └── ...
    ├── munin/ # module de Munin, utilisé pour le monitoring
    │   └── ...
    ├── pages/ # module pour les autres pages, telles que la page d'accueil, ...
    │   └── ...
    ├── search/ # module de recherche
    │   └── ...
    ├── tutorial/ # module des tutoriels
    │   └── ...
    ├── utils/ # fonctions utiles à chaque module
    │   └── ...
    ├── middlewares/ # codes provenant de sources externes
    │   └── ...

On retrouve également dans ce dossier les quelques fichiers suivants, nécessaires à la configuration et au fonctionnement de Django :

.. sourcecode:: bash

    zds/
    ├── urls.py # définition générale des URLs du site, inclus celle de chacun des modules
    └── wsgi.py

Contenu d'un module
===================

Chacun des modules possède dans son dossier une arborescence fort semblable, et dans laquelle il est possible de trouver:

.. sourcecode:: bash

    module/
    ├── migrations/
    │   └── ...
    ├── api/
    │   └── ...
    ├── tests/
    │   ├── tests.py
    │   └── ...
    ├── admin.py
    ├── commons.py
    ├── factories.py
    ├── feeds.py
    ├── forms.py
    ├── managers.py
    ├── models.py
    ├── search_indexes.py
    ├── urls.py
    └── views.py

Fichiers principaux
-------------------

Django étant basé sur une architecture de type Modèle-Vue-Template, on retrouve les modèles dans le fichier ``models.py`` et les contrôles associés à celles-ci dans ``views.py``. Ces dernières peuvent employer des classes formulaires qui sont définis dans ``forms.py``. Les URLs associées au module et permetant d'accéder aux vues sont définies dans ``urls.py``. On retrouve finalement des vues spécifiques associées aux fils RSS et Atom dans ``feeds.py``.

On retrouve également des validateurs dans le fichier ``commons.py`` (voir à ce sujet `la documentation de Django <https://docs.djangoproject.com/fr/1.8/ref/validators/>`__).

Tests unitaires
---------------

Une partie importante du développement est basée sur les tests unitaires : afin d'éviter qu'un développement futur ne brise une fonctionnalité, une série de test associé à chaque module est écrite dans des fichiers situés dans le dossier ``tests/`` de chaque module. Cette série de test peut être lancée en utilisant la commande suivante :

.. sourcecode:: bash

    python manage.py test zds.module

où il est nécéssaire de remplacer ``module`` par le nom du module associé. Ces tests utilisent des données de tests générées par des *factories* (usines) qui sont définies dans ``factories.py``.

Gestion de la base de données
-----------------------------

Le dossier ``migrations/`` permet à Django de consigner les changements effectués à des modèles qui modifient également la structure de la base de donnée. Son contenu ne devrait pas être modifié manuelement, il l'est cependant de manière automatique lorsque la commande suivante est utilisée :

.. sourcecode:: bash

    python manage.py makemigrations

Celle-ci doit être utilisée lorsqu'une variable d'un modèle (dans ``models.py``) est modifiée, ajoutée ou supprimée. Si tel est le cas, n'oubliez pas d'inclure le fichier résultant (de la forme ``xxxx_auto_yyy.py``) dans votre prochain *commit* !

Cela permettra aux autres développeurs de répercuter les modifications en utilisant:

.. sourcecode:: bash

    python manage.py migrate --fake-initial


API
---

Une description fonctionnelle de l'API est faite `sur la page correspondante <../api.html>`__.

Les fichiers correspondants à une API du module (si elle existe) se situent dans le dossier ``api/``. Dans celui-ci, se trouvent principalement de nouvelles vues (``api/views.py``), URLs (``api/urls.py``) et tests (``api/tests.py``). On retrouve également des *serializers* dans ``api/serializers.py``, nécessaires à la création de l'API (voir à ce sujet `la documentation du REST framework (en) <http://www.django-rest-framework.org/api-guide/serializers/>`__).


Autres
------

Le fichier ``search_index.py`` est utilisé par Django pour générer les *index* de recherche pour `Solr <../install/install-solr.html>`__.

Le fichier ``admin.py`` est quand à lui employé par Django pour la partie administration (accessible en local via ``/admin/``).
