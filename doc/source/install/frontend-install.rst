========================
Installation du frontend
========================

Vous voulez nous aider au développement du frontend ? Installez Node.js et npm grâce aux instructions qui suivent !


Installation de Node.js et npm
==============================

Le frontend de Zeste de Savoir repose sur la version supportée à long terme actuelle de Node.js, la version 4.

L'installation de ``node`` est détaillée sur le site de Node.js, soit par `téléchargement direct <https://nodejs.org/en/download/>`_, soit via un `gestionnaire de paquet <https://nodejs.org/en/download/package-manager/>`_. Zeste de Savoir requiert la version 4, mais marche également avec la version 6.

Vérifier que les bonnes versions sont installées
------------------------------------------------

Pour vérifier que Node.js et npm sont installés (et que vous avez les bonnes versions) :

.. sourcecode:: bash

    node -v
    v4.x.x
    npm -v
    2.14.12 # n'importe quelle version plus grande que 1.x

**Vous devez avoir une version de Node.js v4.x et de npm 2 ou supérieure.** Si votre version de npm est 1.x.x, vous devez le mettre à jour (voir juste en dessous).

Mise à jour de Node.js et npm
-----------------------------

Pour npm, il suffit de le mettre à jour avec cette commande :

.. sourcecode:: bash

    npm install -g npm # si ça échoue, retentez avec sudo

Pour ce qui est de Node.js, une mise à jour via le gestionnaire de paquets devrait fonctionner.

.. note::
   En cas de gros pépin avec l'installation de npm, il peut arriver que ce dernier soit complètement en vrac. Dans ce genre de situation, ce `lien StackOverflow <http://stackoverflow.com/questions/31025048/npm-doesnt-work-get-always-this-error-error-cannot-find-module-are-we-ther>`_ peut vous sauver ;) .


Installation des dépendances npm
--------------------------------

L'installation de Gulp, ainsi que des différentes dépendances et bibliothèques, se fait via npm dans le répertoire du projet :

.. sourcecode:: bash

    make install-front # ou la commande suivante :
    npm install


Utilisation des outils
======================

Vous avez installé les outils ? Voilà comment on s'en sert dans notre projet !

**Note :** dans la suite de ce document, les utilisateurs d'OS X et de GNU/Linux préféreront utiliser ``make``, les utilisateurs de Windows qui ne connaissent pas ``make`` préféreront utilise ``npm`` directement.

Présentation de Gulp
--------------------

Gulp est un outil permettant d'automatiser les tâches liées au *front-end*. Dans notre cas, il permet de :

- vérifier la syntaxe Javascript ;
- minimiser les fichiers Javascript et les rassembler en un fichier ;
- compiler les fichiers SCSS pour les transformer CSS ;
- compresser les images et créer un sprite.

Utilisation de Gulp
-------------------

Gulp se lance avec ``npm run gulp -- [tâche]`` où ``[tâche]`` est la tâche à lancer.

Générer les fichiers avec ``build``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Saisissez la commande suivante (elle vous permet de générer les fichiers Web du site pour vous permettre de consulter Zeste de Savoir sur votre navigateur, en local) :

.. sourcecode:: bash

    # Au choix, en fonction de votre environnement :
    make build-front
    npm run build

``build`` permet de :

- minimiser les fichiers Javascript et les rassembler en un fichier ;
- compiler les fichiers SCSS pour les transformer CSS ;
- compresser les images et créer un sprite.

Les fichiers générés sont disponibles dans le dossier ``dist/`` (un aperçu est disponible
`ici <../front-end/arborescence-des-fichiers.html>`_).

.. note::
   C'est la tâche que vous utiliserez sûrement le plus souvent car vous devez la lancer à chaque modification
   de ``assets/`` !

Si vos modifications n'apparaissent pas dans votre navigateur et que ce n'est pas dû à Gulp, pensez à vider le
cache de votre navigateur !

Supprimer les fichiers générés avec ``clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``clean`` supprime les fichiers générés par ``build`` (il supprime simplement le dossier ``dist/``).

``make clean-front`` ou ``npm run clean``

Vérifier le code avec ``lint``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``lint`` vérifie, par le biais de JSHint, la forme du code (indentation, doubles guillemets, etc). Si le code ne
respecte pas ces règles, le script va sortir une liste d'erreurs (*errors*) et/ou d'avertissements (*warnings*)
que vous devez corriger.

.. note::
   L'outil d'intégration continue que nous utilisons, Travis CI, fait cette vérification à la création de chaque *pull
   request* et sortira la liste des erreurs et des avertissements. Pour éviter d'attendre qu'il ait fini, il est plus
   pratique pour vous (et nous) que vous lanciez cette commande en amont avec ``make lint-front` ou ``npm run test`` (ou
   ``npm test``).

Coder plus simplement avec ``watch``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``watch`` surveille les fichiers SCSS et Javascript lance la tâche ``build`` dès qu'ils sont modifiés. C'est très
utile pour le développement car ça permet de ne pas avoir à relancer ``build`` manuellement. Pour lancer cette commande, faites ``make watch-front`` ou ``npm run watch``. Pour arrêter cette commande, il suffit de presser ``Ctrl+C``.

-----

.. seealso::

    Vous voulez en savoir plus ?
    Venez voir `la documentation consacrée au front-end <../front-end.html>`_ ! ;)

Nettoyage des outils
====================

Désinstaller les dépendances
----------------------------

Il vous suffit pour cela de lancer la commande :

.. sourcecode:: bash

    npm uninstall

Si ça ne fonctionne pas, vous pouvez le faire manuellement grâce à ``rm -rI node_modules/``.

Désinstaller les dépendances inutilisées
----------------------------------------

Il y a une commande toute faite pour ça :

.. sourcecode:: bash

    npm prune
