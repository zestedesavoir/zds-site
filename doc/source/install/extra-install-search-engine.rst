===================================
Installation du moteur de recherche
===================================

Zeste de Savoir utilise **Typesense** comme moteur de recherche. L'installer
est nécessaire pour faire fonctionner la recherche.


Installation
============

Vous pouvez suivre les instructions fournies dans `la documentation officielle
<https://typesense.org/docs/guide/install-typesense.html>`_ (*Option 2: Local
Machine / Self-Hosting*).



Indexation et recherche
=======================

Pour tester que tout fonctionne, quand Typesense est démarré, rendez-vous sur
la page `http://localhost:8108/health <http://localhost:8108/health>`_. Vous
devriez observer une réponse du même genre que celle-ci :

.. sourcecode:: none

    {"ok":true}

Si ce n'est pas le cas, vérifiez que Typesense est correctement démarré.

Si c'est le cas, vous pouvez indexer les données à l'aide de la commande
``search_engine_manager``, comme suit :

.. sourcecode:: bash

    python manage.py search_engine_manager index_all

Une fois que c'est fait, en vous rendant sur la page de recherche de Zeste de
Savoir, `http://localhost:8000/rechercher/
<http://localhost:8000/rechercher/>`_, vous devriez pouvoir d'utiliser la
recherche. En particulier, vous ne devriez pas observer de message d'erreur :

.. figure:: ../images/search/no-connection.png
    :align: center

    Si Typesense n'est pas démarré, un message d'erreur apparait.

Pour indexer uniquement les nouvelles données, utilisez la commande suivante :

.. sourcecode:: bash

    python manage.py search_engine_manager index_flagged

Plus d'informations sur la commande ``search_engine_manager`` sont disponibles
sur la page `concernant la recherche sur Zeste de Savoir
<../back-end/searchv2.html#indexer-les-donnees-de-zds>`_.
