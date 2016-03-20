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
    │   │   ├── arrow-right-blue.png
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
    │   ├── vendors/  # Toutes les bibliothèques (disponibles après l'installation des outils)
    │   │   ├── jquery.js
    │   │   ...
    │   │
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
    │   ├── only-ie.scss  # Styles pour Internet Explorer 9
    │   ├── sprite-template.mustache  # Fichier servant à la génération du sprite
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
    │   ├── main.css  # Tout le CSS compilé...
    │   └── main.min.css  # ...et minimisé
    │
    ├── images/
    │   ├── sprite@2x.png  # Sprite haute résolution
    │   ├── sprite.png  # Sprite moyenne résolution
    │   │
    │   │ # Images inchangées
    │   ├── favicon.ico
    │   ├── favicon.png
    │   ├── logo@2x.png
    │   ├── logo.png
    │   ...
    │
    ├── js/
    │   ├── vendors/  # Toutes les bibliothèques non-minimisées
    │   │   ├── jquery.js
    │   │   ...
    │   │
    │   ├── vendors.js  # Toutes les bibliothèques rassemblées...
    │   ├── vendors.min.js  # ...et minimisées
    │   │
    │   ├── main.js  # Tout le JS customisé rassemblé...
    │   ├── main.min.js  # ...et minimisé
    │   │
    │   ├── all.js  # Tout le JS rassemblé...
    │   └── all.min.js  # ...et minimisé
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
    │   ├── about.html
    │   ├── contact.html
    │   ...
    │
    ├── misc/  # Dossier contenant des fichiers utilisés dans plusieurs modules
    │   ├── previsualization.part.html  # Ex : la prévisualtion des messages...
    │   ├── zen_button.part.html  # ... ou le bouton de lecture zen
    │   ...
    ...
