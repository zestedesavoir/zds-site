===================================
Installation du moteur de recherche
===================================

Zeste de Savoir utilise **Typesense** comme moteur de recherche. L'installer
est nécessaire pour faire fonctionner la recherche.


Installation
============

La version de Typesense utilisée par ZdS est définie par la variable
``$ZDS_TYPESENSE_VERSION`` dans ``scripts/define_variable.sh``.

Il est possible d'installer Typesense de plusieurs façons, comme indiqué dans
`la documentation officielle
<https://typesense.org/docs/guide/install-typesense.html>`_ (*Option 2: Local
Machine / Self-Hosting*).

Depuis le script d'installation de ZdS
--------------------------------------

Cette méthode fonctionne uniquement sur un système Linux utilisant un processeur avec une architecture amd64.

Exécutez :

.. sourcecode:: bash

    ./scripts/install_zds.sh +typesense-local

Référez-vous à `la documentation correspondante
<./install-linux.html#composant-typesense-local>`_ pour savoir ce que fait
cette commande.

Il faut ensuite lancer Typesense avec la commande suivante :

.. sourcecode:: bash

    make run-search-engine

Avec Docker
-----------

Cette méthode a l'avantage de fonctionner sur n'importe quel système qui dispose de Docker :

.. sourcecode:: bash

    docker run -p 8108:8108 typesense/typesense:$ZDS_TYPESENSE_VERSION --api-key=xyz --data-dir=/tmp

Vérifier le bon lancement de Typesense
======================================

Pour tester que tout fonctionne, quand Typesense est démarré, rendez-vous sur
la page `http://localhost:8108/health <http://localhost:8108/health>`_. Vous
devriez observer une réponse du même genre que celle-ci :

.. sourcecode::

    {"ok":true}

Si ce n'est pas le cas, vérifiez que Typesense est correctement démarré.

Indexation et recherche
=======================

Une fois que Typesense est installé et démarré, vous pouvez indexer les données
à l'aide de la commande ``search_engine_manager``, comme suit :

.. sourcecode:: bash

    python manage.py search_engine_manager index_all

Une fois que c'est fait, en vous rendant sur la page de recherche de Zeste de
Savoir, `http://localhost:8000/rechercher/
<http://localhost:8000/rechercher/>`_, vous devriez pouvoir d'utiliser la
recherche.

Pour indexer uniquement les nouvelles données, utilisez la commande suivante :

.. sourcecode:: bash

    python manage.py search_engine_manager index_flagged

Plus d'informations sur la commande ``search_engine_manager`` sont disponibles
sur la page `concernant la recherche sur Zeste de Savoir
<../back-end/search.html>`_.
