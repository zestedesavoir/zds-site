===================================
Installer Zeste de Savoir sur Linux
===================================

Vous voulez installer Zeste de Savoir sur votre distribution GNU/Linux ? Vous êtes au bon endroit !

Préparation
===========

Préparation pour contribuer au projet
-------------------------------------

Toutes les contributions au projet prennent place sur le site web Github, un espace de travail très connu des projets *open-source*. La première étape est donc de `se créer un compte Github <https://github.com/join>`_ pour contribuer au projet !

La deuxième étape est de créer `un fork <https://help.github.com/en/github/getting-started-with-github/fork-a-repo>`_, votre copie personnelle du projet. Pour ce faire, une fois connecté à votre compte Github, rendez-vous sur `la page du dépôt zds-site <https://github.com/zestedesavoir/zds-site>`_ et cliquez sur le bouton *Fork* en haut à droite. Cette opération peut prendre quelques minutes, c'est tout à fait normal.

La troisème étape consiste à installer le gestionnaire de version Git, un outil qui nous permet de travailler à plusieurs sur le projet sans se marcher dessus ! Ce logiciel est très probablement disponible dans le gestionnaire de paquet de votre distribution. Si ce n'est pas le cas, je vous invite à lire `la page d'installation de Git <https://git-scm.com/downloads>`_.

Enfin, la quatrième étape est la création d'une copie locale du projet, sur votre ordinateur, en utilisant l'outil Git fraîchement installé :

.. sourcecode:: bash

   git clone https://github.com/<VOTRE_PSEUDO_GITHUB>/zds-site.git
   cd zds-site
   git remote add upstream https://github.com/zestedesavoir/zds-site.git
   git fetch upstream

Bien entendu, ``<VOTRE_PSEUDO_GITHUB>`` doit être remplacé par votre pseudo sur Github.

Voilà, vous avez maintenant une copie locale du projet, liée à votre copie personnelle (*origin*) et la copie officielle (*upstream*) sur Github !

Préparation pour simplement tester le projet
--------------------------------------------

Si vous ne souhaitez pas contribuer au projet mais simplement le tester, vous n'avez pas besoin de Git ! Il vous suffit de télécharger l'archive contenant le code source et extraire les fichiers :

.. sourcecode:: bash

   wget https://github.com/zestedesavoir/zds-site/archive/dev.zip
   unzip dev.zip
   cd dev

Installation de l'utilitaire Make
---------------------------------

Nous utilisons l'utilitaire Make pour avoir des commandes simples à retenir. Celui-ci est très probablement déjà installé sur votre distribution, ce que vous pouvez vérifier tout simplement avec :

.. sourcecode:: bash

   make

S'il est installé, cela vous affichera la liste des commandes de notre projet. Sinon, il vous faudra l'installer avec ``sudo apt install build-essential`` sur Ubuntu et ses dérivés ou `le télécharger sur cette page <https://www.gnu.org/software/make/#download>`_.

Installation
============

Installation de base
--------------------

Si notre projet est assez complexe et a besoin de beaucoup d'outils différents pour fonctionner, ce n'est pas pour autant qu'il est difficile de l'installer ! Une seule commande suffit :

.. sourcecode:: bash

   make install-linux

Et oui, c'est tout !

Dès le lancement, cette commande vous demandera quelle est votre distribution Linux pour savoir quel gestionnaire de paquet utiliser et quels paquets installer. Votre mot de passe d'administrateur vous sera demandé pour pouvoir installer ces paquets.

Ensuite, le reste de l'installation se fait tout seul sans rien vous demander ! En fonction de votre connexion Internet et de la puissance de votre ordinateur cela peut prendre du temps, soyez patient !

**Si vous rencontrez un soucis, n'hésitez pas à nous contacter !**

Installation complète
---------------------

L'installation de base suffit grandement pour lancer le site web et découvrir le projet, mais elle est incomplète. Deux outils manquent à l'appel :

- LaTeX, nécessaire pour la génération des PDFs des contenus ;
- Typesense, nécessaire pour la page de recherche.

Là encore, une seule commande suffit :

.. sourcecode:: bash

   make install-linux-full

En savoir plus sur l'installation
---------------------------------

Si le fonctionnement du script d'installation vous intéresse, je vous invite à lire `cette page détaillée <../install/install-linux.html>`_.

Aller plus loin
===============

Vous avez réussi à installer Zeste de Savoir ? Il est maintenant temps de `le lancer <run-linux.html>`_ !

.. include:: /includes/contact-us.rst
