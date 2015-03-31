==============
Le *front-end*
==============

Le terme *front-end* désigne la partie du code associée à l'affichage des données issues du `back-end <back-end.html>`__.

Il s'agit donc de la partie du code définissant le design et l'affichage, mais aussi de l'ergonomie, la réactivité et l'expérience utilisateur. Sa mise en place est basée sur trois langages :

+ Le HTML, aidé du `langage de template de Django <https://docs.djangoproject.com/en/dev/topics/templates/>`__ ;
+ `SASS <http://sass-lang.com/>`__ pour les feuilles de style ;
+ Javascript pour les interactions.

`NodeJS <https://nodejs.org/>`__, son gestionnaire de packet (`npm <https://www.npmjs.com/>`__) et `Gulp <http://gulpjs.com/>`__ sont utilisés pour générer le code finale minifié et cohérent. Le développement du *front-end* requiert donc des outils spécifiques dont l'instalation `est expliquée ici <install/frontend-install.html>`__.

.. toctree::
   :maxdepth: 2
   :glob:

   front-end/*