=================================================
Installation de Elasticsearch (pour la recherche)
=================================================

Zeste de Savoir utilise **Elasticsearch 5**, un moteur de recherche très performant.
Installer Elasticsearch est nécessaire pour faire fonctionner la recherche.


Installation
============

.. attention::

    Par défaut, Elasticsearch requiert au moins 2 Gio de mémoire pour démarrer.

    Si vous ne souhaitez pas utiliser autant de mémoire, modifiez le fichier ``config/jvm.option``, en particuliez les options ``-Xms`` et ``-Xmx``.
    Par exemple, vous pouvez passer la valeur de ces variables à 512 Mio grâce à:

    .. sourcecode:: none

        -Xms512m
        -Xmx512m

    Plus d'informations sont disponibles `dans la documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/setting-system-settings.html#jvm-options>`_.

Sous Linux
----------

Installer java 8
++++++++++++++++

Il est nécessaire d'utiliser **la version 8** de Java pour faire tourner Elasticsearch, mais ce n'est probablement pas la version par défaut de votre système d'exploitation.

**Sous Debian et dérivés**, le package à installer est ``openjdk-8-jdk`` :

+ Sous Ubuntu (et dérivés), s'il n'est pas disponible pour votre système, ajoutez le PPA suivant : ``add-apt-repository ppa:openjdk-r/ppa`` (**en root**).
+ Sous Debian, il est disponible dans le dépôt ``jessie-backports`` (ajoutez ``deb http://ftp.fr.debian.org/debian jessie-backports main`` dans ``/etc/apt/sources.list``).

Une fois installé, passez sur la version 8 de java à l'aide de ``update-alternatives --config java`` (**en root**).

**Sous Fedora et dérivés** (CentOS, OpenSuse, ...), le paquet à installer est ``java-1.8.0-openjdk``.
Passez ensuite à la version 8 de java à l'aide de la commande ``alternatives --config java`` (**en root**).

Installer Elasticsearch
+++++++++++++++++++++++

La procédure d'installation, si vous souhaitez utiliser Elasticsearch sans l'installer via le gestionnaire de paquets de votre distribution, est d'entrer les commandes suivantes dans votre *shell* préféré:

.. sourcecode:: bash

    wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.5.2.zip
    unzip elasticsearch-5.5.2.zip
    cd elasticsearch-5.5.2/

Pour démarrer Elasticsearch, utilisez

.. sourcecode:: bash

    ./bin/elasticsearch

Vous pouvez arrêter Elasticsearch grâce à CTRL+C.

.. note::

    Vous pouvez également installer Elasticsearch comme *daemon* de votre système.
    Rendez-vous `sur la page d'installation d'Elasticsearch <https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html>`_ pour plus d'informations

Sous macOS
----------

Utilisez les commandes suivantes pour installer Java 8 et Elasticsearch:

.. sourcecode:: bash

    brew update
    brew cask install java
    brew install elasticsearch


Pour démarrer Elasticsearch, utilisez la commande suivante:

.. sourcecode:: bash

    elasticsearch --config=/usr/local/opt/elasticsearch/config/elasticsearch.yml

.. note::

    Vous pouvez également le démarrer comme *daemon*, comme sous Linux.
    Plus d'infos `ici <https://gist.github.com/jpalala/ab3c33dd9ee5a6efbdae>`_.

Sous Windows
------------

Elasticsearch requiert **la version 8** de Java, que vous pouvez trouver `sur la page officielle de java <http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html>`_. Prenez la version correspondante à votre système d'exploitation.

Téléchargez ensuite Elasticsearch à l'adresse suivante : `https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.5.2.zip <https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.5.2.zip>`_, puis extrayez le dossier ``elasticsearch-5.5.2`` du zip à l'aide de votre outil préféré.

Pour démarer Elasticsearch, ouvrez un *shell* (ou un *powershell*) et rendez-vous dans le dossier ``elasticsearch-5.5.2``.
Exécutez ensuite la commande suivante :

.. sourcecode:: bash

    bin\elasticsearch


Vous pouvez arrêter Elasticsearch grâce à CTRL+C, puis en répondant "o" lorsqu'il vous est demandé ``Terminer le programme de commandes (O/N) ?``.

.. note::

    Vous pouvez également le démarrer comme *daemon*, comme sous Linux.
    Plus d'informations `dans la documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/windows.html#windows-service>`_.

Indexation et recherche
=======================

Pour tester que tout fonctionne, quand Elasticsearch est démarré, rendez-vous sur la page `http://localhost:9200/ <http://localhost:9200/>`_.
Vous devriez observer une réponse du même genre que celle-ci :

.. sourcecode:: none

    {
      "name" : "p0bcxqN",
      "cluster_name" : "elasticsearch",
      "cluster_uuid" : "649S5bMUQOyRzYmQFVPA1A",
      "version" : {
        "number" : "5.5.2",
        "build_hash" : "19c13d0",
        "build_date" : "2017-07-18T20:44:24.823Z",
        "build_snapshot" : false,
        "lucene_version" : "6.6.0"
      },
      "tagline" : "You Know, for Search"
    }


Si ce n'est pas le cas, vérifiez que vous avez démarré Elasticsearch.

Si c'est le cas, vous pouvez indexer les données à l'aide de la commande ``es_manager``, comme suit :

.. sourcecode:: bash

    python manage.py es_manager index_all

Une fois que c'est fait, en vous rendant sur la page de recherche, `http://localhost:8000/rechercher/ <http://localhost:8000/rechercher/>`_, vous devriez être capable d'utiliser la recherche.
En particulier, vous ne devriez pas observer de message d'erreur :

.. figure:: ../images/search/no-connection.png
    :align: center

    Si Elasticsearch n'est pas démarré, le message suivant apparait.

Pour réindexer les nouvelles données, utilisez la commande suivante :

.. sourcecode:: bash

    python manage.py es_manager index_flagged

Plus d'informations sur la commande ``es_manager`` sont disponibles sur la page `concernant la recherche sur ZdS <../back-end/searchv2.html#indexer-les-donnees-de-zds>`_.

