=========================
Arborescence des dossiers
=========================

Nous utilisons deux dossiers présents à la racine :

- ``templates/`` pour les fichiers HTML, qui sont agrémentés du `langage de gabarit de Django <https://docs.djangoproject.com/fr/1.7/topics/templates/>`_ ;
- ``assets/`` pour les images, les smileys et les fichiers SCSS et JS.

Lors de la compilation, un dossier ``dist/`` contenant les fichiers optimisés venant de ``assets/`` est créé.


``assets/``
===========

Voici un aperçu du dossier :

.. sourcecode:: bash

    assets/
    ├── images/
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
    ├── js/
    │   ├── vendors/  # Toutes les bibliothèques (disponibles après l'installation des outils)
    │   │   ├── jquery.js
    │   │   ...
    │   │
    │   ├── accessibility-links.js
    │   ├── data-click.js
    │   ...
    │
    ├── scss/
    │   ├── layout/
    │   │   ├── _header.scss
    │   │   ├── _sidebar.scss
    │   │   ...
    │   ├── components/
    │   │   ...
    │   │
    │   ├── main.scss  # Fichier de configuation
    │   ├── sprite-template.mustache  # Fichier servant à la génération du sprite
    │   ...
    │
    └── smileys/
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
    │   ├── chapter/
    │   │   ├── edit.html
    │   │   ├── new.html
    │   │   ...
    │   │
    │   ├── extract/
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
    │   ├── zen_button.part.html
    │   ├── previsualization.part.html
    │   ...
    ...
