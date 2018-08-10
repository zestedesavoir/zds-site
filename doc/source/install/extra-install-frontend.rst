========================
Installation du frontend
========================

Vous voulez nous aider au développement du frontend ? Installez Node.js et Yarn grâce aux instructions qui suivent !


Installation de Node.js et Yarn
===============================

Le frontend de Zeste de Savoir repose sur la version actuelle de Node.js supportée à long terme, la version 8. Vous pouvez installer Node.js 8 via `votre gestionnaire de paquet <https://nodejs.org/en/download/package-manager/>`_ (``apt``, ``yum``, …) ou en téléchargeant une `archive <https://nodejs.org/en/download/>`_.

Dans le cas où vous avez besoin de faire cohabiter sur votre système différentes versions de Node.js pour des projets différents, à l’instar de virtualenv ou rvm, il existe `nvm <https://github.com/creationix/nvm>`_ (Node Version Manager) qui permet d’installer plusieurs version de Node.js et de basculer d’une version à l’autre facilement.

Le gestionnaire de paquet ``npm`` (Node.js Package Manager) est fourni avec Node.js, mais nous préferons utiliser Yarn qui est plus rapide et plus sûr. Yarn n’est strictement nécessaire qu’en production mais nous recommandons également de s'en servir lors du développement. `Installer Yarn <https://yarnpkg.com/fr/docs/install/>`_.

Vérifier que les bonnes versions sont installées
------------------------------------------------

Pour vérifier que Node.js et yarn sont installés (et que vous avez les bonnes versions) :

.. sourcecode:: bash

    $ node -v
    v8.x.x
    $ yarn -v
    0.27.x

Si ``yarn`` n’est pas installé ou pas à jour, utilisez ``npm i -g yarn``.

Si vous désirez utiliser ``npm`` à la place de ``yarn``, vérifiez que vous avez la version 5 ou une plus récente.

Mise à jour de Node.js et Yarn
------------------------------

Pour Yarn, il suffit de le mettre à jour avec cette commande :

.. sourcecode:: bash

    $ npm install -g yarn

Pour ce qui est de Node.js, utilisez soit votre gestionnaire de paquet, soit nvm.


Installation des dépendances Yarn
---------------------------------

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
   pratique pour vous (et nous) que vous lanciez cette commande en amont avec ``make lint-front`` ou ``yarn run test`` (ou
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

Il suffit de supprimer le dossier ``node_modules``:

.. sourcecode:: bash

   rm -r node_modules/.
