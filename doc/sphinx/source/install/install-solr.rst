========================================
Installation de Solr (pour la recherche)
========================================

| Zeste de Savoir utilise Solr, un moteur de recherche très performant développé par la fondation Apache.
| Installer Solr est **nécessaire** pour faire fonctionner la recherche.

Il existe beaucoup de manières d'installer Solr. L'une des plus simples est d'utiliser les exemples embarqués avec le paquet de release.

Prérequis sur linux
===================

Avant toute chose soyez-sûr d'avoir Java (disponible dans les dépôts de votre distribution, ou `sur le site officiel <http://www.java.com/fr/download/manual.jsp#lin>`__).

Téléchargez `l'archive Solr <http://archive.apache.org/dist/lucene/solr/4.9.0/solr-4.9.0.zip>`__ ou entrez la commande ``wget wget http://archive.apache.org/dist/lucene/solr/4.9.0/solr-4.9.0.zip``.

Puis décompressez l'archive avec ``unzip solr-4.9.0.zip``.

Prérequis sur windows
=====================

Avant toute chose soyez-sûr d'avoir `Java <http://www.java.com/fr/download/win8.jsp>`__.

Ajoutez le dossier contenant java à votre PATH : dans "Ordinateur", clic droit puis "Proprétés", ouvrez les "propriétés avancées" puis cliquez sur "Variables d'environnement".

Téléchargez `l'archive Solr <http://archive.apache.org/dist/lucene/solr/4.9.0/solr-4.9.0.zip>`__. Décompressez-la.

Procédure commune
=================

Ouvrez le terminal ou powershell.

A la racine de votre dépot ZdS, lancez la commande :

.. code:: bash

    python manage.py build_solr_schema > %solr_home%/example/solr/collection1/conf/schema.xml

où ``%solr_home%`` est le dossier dans lequel vous avez installé Solr.

Placez-vous dans ce dossier et exécutez :

.. code:: bash

    cd example/
    java -jar start.jar

Vérifiez que solr est fonctionnel en entrant dans votre navigateur l'url http://localhost:8983/solr/

Maintenant que Solr est prêt, allez à la racine de votre dépôt zeste de savoir, une fois votre virtualenv activé, indexez les les données du site :

.. code:: bash

    python manage.py rebuild_index

Une fois terminé, vous avez une recherche fonctionnelle.

Pour mettre à jour un index existant, la commande est :

.. code:: bash

    python manage.py update_index
