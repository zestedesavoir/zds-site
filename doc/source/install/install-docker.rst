========================
Installation dans Docker
========================

Installation via docker-compose
===============================

.. note::

    L'installation à partir de docker-compose est entièrement containeurisée.
    Ce qui signifie que seules les sources de zds-site se trouvent sur votre système
    et tout le reste (dépendances back, front) tournent dans des containeurs séparés.

Installation d'une instance locale vide
---------------------------------------

.. note::

    Cette installation déploie zds sur votre poste local au plus proche de ce qu'on peut avoir sur la production.
    La base de donnée utilisée est mariadb.

Deux prérequis sont necessaires pour installer zds-site par ce moyen.

- `docker-compose <https://docs.docker.com/compose/install/>`_
- `docker <https://docs.docker.com/get-docker/>`_

Après avoir cloné le dépôt du code source, installer ZdS via docker-compose est relativement simple.
En effet, il suffit de lancer la commande suivante (qui se chargera d'installer ce qui est nécessaire sans polluer votre système):

.. sourcecode:: bash

    docker-compose up

.. warning::
    La première fois, la commande sera très longue, le temps de télécharger et construire les images nécessaires.
    Au deuxième lancement, la commande sera beaucoup plus rapide.

Une fois installé et démarré vous pouvez ouvrir votre navigateur à l'addresse suivante : ``http://localhost:8000/`` pour consulter votre version locale de ZdS.

Chargement des fixtures
-----------------------

Une fois zds installé et démarré, vous aurez certainement besoin de charger des fixtures pour avoir des données prêtes à l'emploi.
Pour cela, il suffit de lancer la commande ci-dessous dans un second terminal.

.. sourcecode:: bash

    docker-compose up fixtures

Cette commande permet de charger des données de test.

Toutes les commandes docker-compose
-----------------------------------

Voici la liste des services docker-compose exposés, les ports que ces services exposent sur votre poste local, les dossiers dans lesquels chaque service écrivent sur votre système.

.. list-table:: Liste des services
   :header-rows: 1

   * - Service
     - Port exposés sur l'hote
     - Dossier local en écriture
     - Description
   * - back
     - 8000
     - ``.``
     - Serveur back django
   * - front
     -
     - ``./dist``
     - Service en écoute sur les éléments de front, et build le front à chaque modification.
   * - indexer
     -
     -
     - Service d'indexation des nouveaux contenus dans Elasticsearch.
   * - fixtures
     -
     - ``./contents-private``, ``./contents-public``
     - Service de chargement des fixtures.
   * - doc
     -
     - ``./doc``
     - Service de génération de la documentation.
   * - cache
     -
     -
     - Service de gestion du cache du back-end.
   * - database
     -
     - ``./data_mysql``
     - Service de gestion de la base de donnée mariadb.
   * - elasticsearch
     -
     -
     - Service de gestion du moteur d'indexation Elasticsearch.
   * - watchdog
     -
     -
     - Service de génération des exports de contenus.

Installation dans un container docker
=====================================

.. note::

    Par manque de développeurs utilisant Docker au sein de l'équipe de
    développement de ZdS, cette section n'est guère fournie. Les instructions
    données ici ne le sont qu'à titre indicatif. N'hésitez pas à signaler tout
    problème ou proposer des améliorations !

L'installation de l'environnement de développement dans Docker se base sur `l'installation sous Linux <install-linux.html>`_.

Lancez un shell interactif dans un conteneur basé sur Debian :

.. sourcecode:: bash

    docker run -it -p 8000:8000 debian:bookworm


Une fois dans le conteneur, saisissez les commandes suivantes :

.. sourcecode:: bash

    # On se place dans le $HOME
    cd

    # Permet d'utiliser correctement apt
    DEBIAN_FRONTEND=noninteractive

    # Installez les paquets minimaux requis
    apt update
    apt install sudo make vim git

    # Clonez le dépôt de ZdS
    git clone https://github.com/<votre login>/zds-site.git
    cd zds-site/

    # Installez ZdS
    make install-linux

    # Nécessaire pour avoir nvm dans le PATH
    source ../.bashrc

    # À partir de maintenant, les commandes ne sont plus spécifiques à l'utilisation de Docker.

    # Lancement de ZdS
    source zdsenv/bin/activate
    make zmd-start
    make run-back
