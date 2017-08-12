========================
Installation du frontend
========================

Vous voulez nous aider au développement du frontend ? Installez Node.js et Yarn grâce aux instructions qui suivent !


Installation de Node.js et Yarn
==============================

Le frontend de Zeste de Savoir repose sur la version supportée à long terme actuelle de Node.js, la version 8.

L'installation de ``node`` est détaillée sur le site de Node.js, soit par `téléchargement direct <https://nodejs.org/en/download/>`_, soit via un `gestionnaire de paquet <https://nodejs.org/en/download/package-manager/>`_. Zeste de Savoir requiert la version 8.

Alternativement, l’installation de Node.js avec `nvm <https://github.com/creationix/nvm>`_ est relativement simple. De plus, nvm permet très facilement de basculer d’une version à une autre.

Yarn peut être installé avec `npm i -g yarn` ou `en suivant ces instructions <https://yarnpkg.com/fr/docs/install/>`_.



Vérifier que les bonnes versions sont installées
------------------------------------------------

Pour vérifier que Node.js et yarn sont installés (et que vous avez les bonnes versions) :

.. sourcecode:: bash

    $ node -v
    v8.x.x
    $ yarn -v
    0.27.x

Si `yarn` n’est pas installé ou pas à jour, utilisez `npm i -g yarn`.

Mise à jour de Node.js et Yarn
-----------------------------

Pour Yarn, il suffit de le mettre à jour avec cette commande :

.. sourcecode:: bash

    $ npm install -g yarn

Pour ce qui est de Node.js, utilisez soit votre gestionnaire de paquet, soit nvm.


Installation des dépendances Yarn
--------------------------------

L'installation de Gulp, ainsi que des différentes dépendances et bibliothèques, se fait via Yarn dans le répertoire du projet :

.. sourcecode:: bash

    $ make install-front

Ou alors :

.. sourcecode:: bash

    $ yarn


Utilisation des outils
======================

Vous avez installé les outils ? Voilà comment on s'en sert dans notre projet !

**Note :** dans la suite de ce document, les utilisateurs d'OS X et de GNU/Linux préféreront utiliser ``make``, les utilisateurs de Windows qui ne connaissent pas ``make`` préféreront utiliser ``yarn`` directement.


Présentation de Gulp
--------------------

Gulp est un outil permettant d'automatiser les tâches liées au *front-end*. C’est une sorte de Makefile.

Utilisation de Gulp
-------------------

Gulp se lance avec ``yarn run gulp -- [tâche]`` où ``[tâche]`` est la tâche à lancer.

Générer les fichiers avec ``build``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Saisissez la commande suivante (elle vous permet de générer les fichiers Web du site pour vous permettre de consulter Zeste de Savoir sur votre navigateur, en local) :

.. sourcecode:: bash

    $ make build-front

Ou alors :

.. sourcecode:: bash

    $ yarn run build

``build`` permet de :

- minimiser les fichiers Javascript et les rassembler en un seul fichier ;
- compiler les fichiers SCSS pour les transformer CSS ;
- compresser les images et créer un sprite.

Les fichiers générés sont disponibles dans le dossier ``dist/`` (un aperçu est disponible `ici <../front-end/arborescence-des-fichiers.html>`_).

.. note::
   C'est la tâche que vous utiliserez sûrement le plus souvent car vous devez la lancer à chaque modification
   de ``assets/`` !

Si vos modifications n'apparaissent pas dans votre navigateur et que ce n'est pas dû à Gulp, pensez à vider le cache de votre navigateur !

Supprimer les fichiers générés avec ``clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``clean`` supprime les fichiers générés par ``build`` (il supprime simplement le dossier ``dist/``).

``make clean-front`` ou ``yarn run clean``

Vérifier le code avec ``lint``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``lint`` vérifie, par le biais de JSHint, la forme du code (indentation, doubles guillemets, etc). Si le code ne
respecte pas ces règles, le script va sortir une liste d'erreurs (*errors*) et/ou d'avertissements (*warnings*)
que vous devez corriger.

.. note::
   L'outil d'intégration continue que nous utilisons, Travis CI, fait cette vérification à la création de chaque *pull
   request* et sortira la liste des erreurs et des avertissements. Pour éviter d'attendre qu'il ait fini, il est plus
   pratique pour vous (et nous) que vous lanciez cette commande en amont avec ``make lint-front` ou ``yarn run test`` (ou
   ``yarn test``).

Coder plus simplement avec ``watch``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``watch`` surveille les fichiers SCSS et Javascript lance la tâche ``build`` dès qu'ils sont modifiés. C'est très utile pour le développement car ça permet de ne pas avoir à relancer ``build`` manuellement. Pour lancer cette commande, faites ``make watch-front`` ou ``yarn run watch``. Pour arrêter cette commande, il suffit de presser ``Ctrl+C``.

-----

.. seealso::

    Vous voulez en savoir plus ?
    Venez voir `la documentation consacrée au front-end <../front-end.html>`_ ! ;)

Nettoyage des outils
====================

Désinstaller les dépendances
----------------------------

.. sourcecode:: bash

   rm -r node_modules/.
