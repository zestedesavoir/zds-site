================================
Lancer Zeste de Savoir sur Linux
================================

Vous avez réussi à `installer Zeste de Savoir sur votre distribution GNU/Linux <install-linux.html>`_ ? Il est maintenant temps de le lancer !

Si cela fait déjà un moment, n'hésitez pas à `mettre à jour votre environnement de développement <update-env.html>`_ avant de suivre ce guide.

Activer l'environnement
=======================

La première chose à faire avant de pouvoir travailler sur le projet est de se déplacer dans le dossier du projet et d'activer l'environnement :

.. sourcecode:: bash

   source zdsenv/bin/activate

Cet environnement permet de ne pas polluer votre distribution avec les logiciels installés spécifiquement pour Zeste de Savoir et de ne pas interférer avec vos autres projets de développement.

Lancer zmarkdown
================

Si vous souhaitez écrire des messages sur le forum, des commentaires, des messages privés ou rédiger des contenus, il est nécessaire de lancer le serveur zmarkdown :

.. sourcecode:: bash

   make zmd-start

Lorsque vous aurez fini, vous pourrez l'arrêter avec :

.. sourcecode:: bash

   make zmd-stop

Lancer le serveur
=================

Il suffit tout simplement d'écrire :

.. sourcecode:: bash

   make run

Ensuite, ouvrez votre navigateur et aller au choix sur http://localhost:8000 ou http://127.0.0.1:8000.

Vous pouvez vous connecter avec le membre ``user``, le membre ``staff`` ou n'importe quel autre membre présent sur http://localhost:8000/membres/ ; le mot de passe est toujours identique au pseudo.

.. note::

	Par défaut, le serveur de développement met en cache dans le navigateur tous les fichiers statiques, sauf les ``.js`` et les ``.css``. Si vous voulez accélérer votre instance locale en mettant le plus de choses possible en cache et en désactivant les outils de développement un peu lourds (à savoir, la *debug toolbar*), vous pouvez utiliser ``make run-fast``. Attention qu'alors, pour avoir la dernière version des fichiers CSS et JS, il vous faudra actualiser de force (``Ctrl+F5`` ou similaire).

S'amuser
========

Votre instance locale de Zeste de Savoir vous appartient, vous êtes libre d'y faire tout ce que vous souhaitez ! N'hésitez pas à explorer les fonctionnalités que vous connaissez moins : la validation des contenus, la modération des messages et des membres, etc. Ainsi, vous aurez un aperçu global des fonctionnalités !

.. include:: ../includes/contact-us.rst
