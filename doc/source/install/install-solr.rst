========================================
Installation de Solr (pour la recherche)
========================================

Zeste de Savoir utilise Solr, un moteur de recherche très performant développé par la fondation Apache. Installer Solr est **nécessaire** pour faire fonctionner la recherche.

Il existe beaucoup de manières d'installer Solr. L'une des plus simples est d'utiliser les exemples embarqués avec le paquet de release.

Prérequis sur linux
===================

Avant toute chose soyez-sûr d'avoir Java (disponible dans les dépôts de votre distribution, ou `sur le site officiel <http://www.java.com/fr/download/manual.jsp#lin>`__).

Téléchargez `l'archive Solr <http://archive.apache.org/dist/lucene/solr/4.9.1/solr-4.9.1.zip>`__ ou entrez la commande ``wget http://archive.apache.org/dist/lucene/solr/4.9.1/solr-4.9.1.zip``.

Puis décompressez l'archive avec ``unzip solr-4.9.1.zip``.

Prérequis sur windows
=====================

Avant toute chose soyez-sûr d'avoir `Java <http://www.java.com/fr/download/win8.jsp>`__.

Ajoutez le dossier contenant java à votre PATH : dans "Ordinateur", clic droit puis "Proprétés", ouvrez les "propriétés avancées" puis cliquez sur "Variables d'environnement".

Téléchargez `l'archive Solr <http://archive.apache.org/dist/lucene/solr/4.9.1/solr-4.9.1.zip>`__. Décompressez-la.

Procédure commune
=================

Ouvrez le terminal ou powershell

.. code:: bash

    python manage.py build_solr_schema > %solr_home%/example/solr/collection1/conf/schema.xml

où ``%solr_home%`` est le dossier dans lequel vous avez installé Solr.

Démarrez ensuite Solr :

.. code:: bash

   cd %solr_home%/example/
   java -jar start.jar

Vérifiez que solr est fonctionnel en entrant dans votre navigateur l'url `http://localhost:8983/solr/ <http://localhost:8983/solr/>`__.

Maintenant que Solr est prêt, allez à la racine de votre dépôt zeste de savoir, une fois votre virtualenv activé, indexez les les données du site :

.. code:: bash

    python manage.py rebuild_index

Une question vous est alors posée :

.. code:: bash

    WARNING: This will irreparably remove EVERYTHING from your search index in connection 'default'.
    Your choices after this are to restore from backups or rebuild via the `rebuild_index` command.
    Are you sure you wish to continue? [y/N]

Répondez "y". Quand c'est fait, l'index est créé et vous avez une recherche fonctionnelle.

Pour mettre à jour les informations sur les contenus (tutoriels et articles), il vous faudrait utiliser la commande:

.. code:: bash

    python manage.py index_content --only-flagged

Pour mettre à jour un index existant, la commande est :

.. code:: bash

    python manage.py update_index

