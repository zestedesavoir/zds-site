==============
Le *front-end*
==============

Le terme *front-end* désigne la partie du code associée à l'affichage des données issues du `back-end <back-end.html>`__.

Il s'agit donc de la partie du code définissant le design et l'affichage, mais aussi de l'ergonomie, la réactivité et l'expérience utilisateur. Sa mise en place est basée sur trois langages :

+ Le HTML, aidé du `langage de gabarit de Django <https://docs.djangoproject.com/fr/1.7/topics/templates/>`__ ;
+ `SASS (en) <http://sass-lang.com/>`__ pour les feuilles de style ;
+ Javascript pour les interactions.

`NodeJS (en) <https://nodejs.org/>`__, `NPM (en) <https://www.npmjs.com/>`__ (gestionnaire de paquet pour NodeJS) et `Gulp (en) <http://gulpjs.com/>`__ sont utilisés pour générer le code final minifié et cohérent. Le développement du *front-end* requiert donc des outils spécifiques dont l'installation `est expliquée ici <install/frontend-install.html>`__.

Pour éviter d'installer les outils front en production pour des questions de fiabilité, le front est automatiquement généré par travis et poussé sur le dépot dès qu'un tag (qui correspond à une release) est poussé sur GitHub. `scripts/push_front.sh <https://github.com/zestedesavoir/zds-site/tree/dev/scripts/push_front.sh>`__ est donc lancé avec l'utilisateur `ZDS-Bot <https://github.com/zds-bot>`__ dès qu'un tag est poussé sur le dépot. Ce script crée un nouveau tag avec *-build* en suffixe, contenant un commit avec le front généré, qui sera déployé en (pré-)production.

.. toctree::
   :maxdepth: 2
   :glob:

   front-end/*
