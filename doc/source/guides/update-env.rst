================================================
Mettre à jour son environnement de développement
================================================

Vous n'avez pas participé au projet depuis quelque temps ? Suivez ce guide pour mettre à jour votre environnement de développement !

Récupérer les dernières modifications
=====================================

Il va falloir utiliser l'utilitaire Git pour :

1. mettre à jour la copie locale du dépôt officiel (nommée ``upstream``) ;
2. se positionner sur la branche ``dev`` de cette copie.

.. sourcecode:: bash
   :linenos:

   git fetch upstream
   git checkout upstream/dev

Activer l'environnement
=======================

La première chose à faire avant de pouvoir travailler sur le projet est de se déplacer dans le dossier du projet et d’activer l’environnement :

.. sourcecode:: bash

   source zdsenv/bin/activate

Cet environnement permet de ne pas polluer votre distribution avec les logiciels installés spécifiquement pour Zeste de Savoir et de ne pas interférer avec vos autres projets de développement.

Mettre à jour les dépendances
=============================

Ces trois commandes permettent de mettre à jour :

1. les paquets Python nécessaires pour le serveur (*backend*) ;
2. les paquets Node.JS nécessaires pour les éléments graphiques (*frontend*) ;
3. zmarkdown, notre moteur Markdown personnalisé.

.. sourcecode:: bash
   :linenos:

   make install-back
   make install-front
   make zmd-install

Générer les éléments graphiques
===============================

Les éléments graphiques ont probablement été modifiés, il va falloir les générer à nouveau :

.. sourcecode:: bash

   make build-front

Appliquer les migrations sur la base de données
===============================================

Il est possible que la structure de la base de données ait été légèrement modifiée, il nous faut donc appliquer ces changements :

.. sourcecode:: bash

   make migrate-db

Aller plus loin
===============

Votre environnement de développement est maintenant à jour, vous pouvez donc `lancer Zeste de Savoir <run-linux.html>`_ !

.. include:: /includes/contact-us.rst
