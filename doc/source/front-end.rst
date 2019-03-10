==============
Le *front-end*
==============

Le terme *front-end* désigne la partie du code associée à l'affichage des données issues du `back-end <back-end.html>`__.

Il s'agit donc de la partie du code définissant le design et l'affichage, mais aussi de l'ergonomie, la réactivité et l'expérience utilisateur. Sa mise en place est basée sur trois langages :

+ Le HTML, aidé du `langage de gabarit de Django <https://docs.djangoproject.com/fr/2.1/topics/templates/>`__ ;
+ `SASS (en) <http://sass-lang.com/>`__ pour les feuilles de style ;
+ JavaScript pour les interactions.

`Node.js (en) <https://nodejs.org/>`__, `yarn (en) <https://yarnpkg.com/en/>`__ (gestionnaire de paquet pour Node.js) et `Gulp (en) <http://gulpjs.com/>`__ sont utilisés pour générer le code final minifié et cohérent. Le développement du *front-end* requiert donc des outils spécifiques dont l'installation `est expliquée ici <install/frontend-install.html>`__.

.. toctree::
   :maxdepth: 2
   :glob:

   front-end/*
