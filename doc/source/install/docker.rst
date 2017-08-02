======
Docker
======

Il est possible de faire tourner facilement ZdS avec Docker et
docker-compose. Notez que c’est encore un peu expérimental.


Démarrage rapide
----------------

`Installez Docker et docker-compose`__ (vous aurez besoin des deux).

.. __: https://docs.docker.com/compose/install/

Clonez le dépot de ZdS avec Git et rendez-vous dans le dossier cloné :

.. code-block:: sh

   $ cd zds-site

Installez et démarrer le site :

.. code-block:: sh

   $ ./clem up

Ce script ``clem`` va se charger de télécharger toutes les
dépendances, de démarrer les conteneurs Docker et de tout installer
automatiquement. Ceci peut prendre un certain temps.

À la fin, les migrations sont appliquées et vous pourrez accéder au
site à l’addresses http://localhost:8000.

Appuyez sur Ctrl+C pour tout arrêter.


Commandes principales de ``clem``
---------------------------------

``./clem --help``
   Affiche une courte aide et liste les commandes disponibles. Vous
   pouvez aussi utiliser cette option sur une commande spécifique.

``./clem up``
   Démarre ZdS. Écoute par défaut sur le port 8000. Vous pouvez
   utiliser un autre port avec ``--port 1234``.

``./clem test back``
   Lance les tests du backend. Tous les arguments suivants sont passés
   au framework de test de Django. Par
   exemple, ``./clem test back zds.member`` lance uniquement les tests
   des membres.

``./clem test front``
   Lance les tests du frontend. Tous les arguments suivants sont aussi
   passés à Gulp (mais comme il n’y a pas de tests, pour l’instant
   ce n’est pas très utile).

``./clem fixture``
   Applique des fixtures. Par défaut, toutes les fixtures sont appliquées
   mais vous pouvez spécifier un nom de
   fichier : ``./clem fixture fixtures/users.yaml``.
   À utiliser pendant que le backend tourne.

``./clem wipe``
   Supprime la base de données.

``./clem lint back``
   Lint le backend.

``./clem lint frontend``
   Lint le frontend.

``./clem lint all``
   Lint le backend et le frontend.

``./clem es``
   Lance des commandes de `manage.py es_manager` (pour Elasticsearch).
   À utiliser pendant que le backend et Elasticsearch tournent.


Notez que ces commandes ne sont pas toutes conçues pour être lancées
en parallèle. Mais en pratique, vous pouvez par exemple lancer
``./clem up`` dans un terminal et pendant ce temps lancer ``./clem
test back`` dans un autre.
