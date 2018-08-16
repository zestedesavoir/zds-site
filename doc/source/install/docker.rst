======
Docker
======

Il est possible de faire tourner facilement ZdS avec Docker et
docker-compose.

.. note::

   Notez que c’est encore un peu expérimental.


Démarrage rapide
----------------

`Installez Docker et docker-compose`__ (vous aurez besoin des deux).

.. __: https://docs.docker.com/compose/install/

Clonez le dépot de ZdS avec Git et rendez-vous dans le dossier cloné :

.. code-block:: sh

   $ cd zds-site

Installez et démarrer le site :

.. code-block:: sh

   $ ./make docker-back-start

Ce script va se charger de télécharger toutes les
dépendances, de démarrer les conteneurs Docker et de tout installer
automatiquement.

.. warning::

   Ceci peut prendre un certain temps la première fois que vous lancer cette commande, puisqu'il faut télécharger
   les containers.

À la fin, les migrations sont appliquées et vous pourrez accéder au
site à l’addresses http://localhost:8000.

Appuyez sur Ctrl+C pour tout arrêter.

Des données de test
-------------------

Pour avoir un jeu de données qui vous permette de travailler, vous pouvez lancer la commande suivante:

.. code-block:: sh

   $ make docker-fixtures

.. warning::

   Cette commande peut prendre aussi un certain temps.

A la fin, vous disposerez des utilisateurs de test listés sur `cette page`_.

.. _cette page: ../utils/fixture_loaders.html#le-chargement-de-jeux-de-donnees-fixtures

Commandes principales
---------------------

Installer le site via docker vous oblige a passer uniquement par des commandes docker pour
le reste de vos actions. Donc dans le Makefile, vous ne pourrez utiliser que les commandes ``make docker-*``.

- ``make docker-back-start`` : Démarre ZdS. Écoute par défaut sur le port 8000.
- ``make docker-back-test`` : Lance les tests du backend.
- ``make docker-front-test``: Lance les tests du frontend.
- ``make docker-fixture`` : Applique des fixtures et indexe les données dans elasticsearch. À utiliser pendant que le backend tourne.
- ``make docker-wipe`` : Supprime la base de données et les contenus.
- ``make docker-back-lint`` : Lint le backend.
- ``make docker-front-lint`` : Lint le frontend.


.. note::

   Notez que ces commandes ne sont pas toutes conçues pour être lancées
   en parallèle.
