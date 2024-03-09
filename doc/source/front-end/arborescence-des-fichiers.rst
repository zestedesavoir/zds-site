=========================
Arborescence des dossiers
=========================

Nous utilisons deux dossiers présents à la racine :

- ``templates/`` pour les fichiers HTML, qui sont agrémentés du `langage de gabarit de Django <https://docs.djangoproject.com/fr/1.8/topics/templates/>`_ ;
- ``assets/`` pour les images, les smileys ainsi que les fichiers SCSS et JS.

Lors de la compilation, un dossier ``dist/`` contenant les fichiers optimisés venant de ``assets/`` est créé.


``assets/``
===========

Voici un aperçu du dossier :

.. sourcecode:: bash

    assets/
    ├── images/  # Images
    │   ├── sprite/  # Images qui seront dans le sprite
    │   │   ├── arrow-right.png
    │   │   ├── arrow-right@2x.png # Version rétina de chaque élément du sprite
    │   │   ├── arrow-right-blue.png
    │   │   ├── arrow-right-blue@2x.png
    │   │   ...
    │   │
    │   │ # Autres images
    │   ├── favicon.ico
    │   ├── favicon.png
    │   ├── logo@2x.png  # Logo haute résolution
    │   ├── logo.png  # Logo moyenne résolution
    │   ...
    │
    ├── js/  # Fichiers Javascript
    │   ├── editor.js
    │   ├── markdown-help.js
    │   ├── modal.js
    │   ├── zen-mode.js
    │   ...
    │
    ├── scss/  # Fichiers SCSS
    │   ├── base/  # Styles de base pour tout le site
    │   ├── components/  # Commposants spécifiques
    │   │   ├── _editor.scss  # Ex : l'éditeur
    │   │   ...
    │   ├── layout/  # Styles pour la structure du site
    │   │   ├── _header.scss  # Ex : l'en-tête...
    │   │   ├── _sidebar.scss  # ... ou la barre latérale
    │   │   ...
    │   ├── mixins/  # Mixins SCSS
    │   ├── pages/  # Styles pour certaines pages
    │   │   ├── _home.scss  # Ex : la page d'accueil
    │   │   ...
    │   ├── variables/  # Variables SCSS
    │   │
    │   ├── main.scss  # Fichier de configuation
    │   ├── zmd.scss  # Feuille de style pour EPUB
    │   ├── _sprite.scss.hbs  # Template Handlebars pour la création du sprite
    │   ...
    │
    └── smileys/  # Smileys
        ├── ange.png
        ├── angry.gif
        ...


``dist/``
=========

Voilà à peu près ce qui est généré lors du "build" :

.. sourcecode:: bash

    dist/
    ├── css/
    │   ├── main.css  # Tout le CSS compilé et minifié
    │   ├── main.map # SourceMap associé
    │   ├── zmd.css  # Feuille de style pour EPUB
    │   └── zmd.map # SourceMap associé
    │
    ├── images/
    │   ├── sprite@2x.png  # Sprite haute résolution
    │   ├── sprite.png  # Sprite moyenne résolution
    │   │
    │   │ # Images compressées
    │   ├── favicon.ico
    │   ├── favicon.png
    │   ├── logo@2x.png
    │   ├── logo.png
    │   ...
    │
    ├── js/
    │   ├── script.js  # Tout le JS concaténé et minifié
    │   └── script.js.map  # SourceMap associé
    │
    └── smileys/
        ├── ange.png
        ├── angry.gif
        ...


``templates/``
==============

Voici un extrait du dossier contenant les gabaris :

.. sourcecode:: bash

    templates/
    ├── tutorial/  # Dossier contenant les gabaris des pages du module des tutoriels
    │   ├── tutorial/
    │   ├── chapter/  # Gabarits pour les chapitres
    │   │   ├── edit.html
    │   │   ├── new.html
    │   │   ...
    │   │
    │   ├── extract/  # Gabarits pour les extraits
    │   │
    │   ├── base.html
    │   ├── export.html
    │   ...
    │
    ├── pages/  # Dossier contenant les pages du site
    │   ├── technologies.html
    │   ├── contact.html
    │   ...
    │
    ├── misc/  # Dossier contenant des fichiers utilisés dans plusieurs modules
    │   ├── preview.part.html  # Ex : la prévisualisation des messages...
    │   ├── zen_button.part.html  # ... ou le bouton de lecture zen
    │   ...
    ...
