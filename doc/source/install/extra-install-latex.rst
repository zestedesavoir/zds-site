=========================================
Installation de LaTeX et de la *template*
=========================================

.. note::

  La procédure peut ne pas fonctionner sous Windows (probable) et macOS (moins probable), où elle n'a pas été testée.
  N'hésitez pas à faire des retours sur `forum des Devs' de Zeste de Savoir <https://zestedesavoir.com/forums/communaute/dev-zone/>`_.


Afin de générer des PDFs, `zmarkdown <https://github.com/zestedesavoir/zmarkdown>`_ est capable de générer du code LaTeX via un plugin nommé `rebber <https://github.com/zestedesavoir/zmarkdown/tree/master/packages/rebber>`_.
Une fois le code généré, il est nécessaire de le compiler, donc d'installer deux composants:

+ Un compilateur LaTeX (en fait, c'est LuaLaTeX qui est employé, mais peu importe ici) ;
+ La *template*, qui permet, entre autres choses, la mise en forme du document (couleurs, page de garde, blocs ...). Celle-ci est située dans un `dépot séparé (en) <https://github.com/zestedesavoir/latex-template>`_, où vous trouverez plus d'informations.


Prérequis
---------

Avant toutes choses, vous devez installer les parties suivantes (peu importe votre système d'exploitation):

+ Les polices `Source Code Pro <https://www.fontsquirrel.com/fonts/source-code-pro>`_ et `Source Sans Pro <https://www.fontsquirrel.com/fonts/source-sans-pro>`_. Une fois téléchargées et décompressées, le programme permetant de visualiser les polices sur votre système d'exploitation propose généralement un bouton d'installation. Sous Linux, vous pouvez simplement employer `ce script <https://github.com/zestedesavoir/latex-template/blob/master/scripts/install_font.sh>`_.
+ Le package `Pygments <http://pygments.org/>`_: vous pouvez l'installer via ``pip`` (``pip install Pygments``, peu importe l'OS) ou via le gestionnaire de package de votre distribution (Linux et macOS). Notez que c'est également une dépendance de ZdS, donc il est déjà installé dans le *virtualenv*.
+ (*optionnel*, Linux seulement) Pour utiliser des formats d'images tels que le GIF ou le SVG, deux outils supplémentaires sont nécessaires: `librsvg <https://github.com/GNOME/librsvg>`_ (souvent disponible sous le nom ``librsvg2-bin`` dans votre gestionnaire de paquets) et `imagemagick <http://www.imagemagick.org/>`_ (probablement disponible via le package du même nom).


Installer une distribution LaTeX
--------------------------------

+ Sous Windows, vous pouvez installer `MikTeX <https://miktex.org/download>`_ ou `TexLive <https://www.tug.org/texlive/>`_.
+ Sous macOS, vous pouvez installer `MacTex <https://www.tug.org/mactex/mactex-download.html>`_.
+ Sous Linux, vous pouvez utiliser `TexLive <https://www.tug.org/texlive/>`_ (qui est probablement disponible dans votre gestionnaire de paquet). Notez que si vous êtes à l'aise, vous pouvez également installer une version allégée, `comme c'est fait ici <https://github.com/zestedesavoir/latex-template/blob/master/scripts/install_texlive.sh>`_ ou `dans le script d'installation automatisé <./install-linux.html##composant-tex-local-et-latex-template>`_.

Si vous n'êtes pas famillier avec LaTeX, choisissez d'installer la version **complète**.
La liste des packages nécessaire `est disponible ici <https://github.com/zestedesavoir/latex-template/blob/master/scripts/packages>`_, mais n'est peut être pas exhaustive.

Installer la *template*
-----------------------

Vous pouvez `télécharger l'archive <https://github.com/zestedesavoir/latex-template/archive/master.zip>`_ et en décompresser le contenu (ou alors cloner le dépot) dans ``<TEXMFHOME>/tex/latex``, où la valeur de ``<TEXMFHOME>`` peut être obtenue en entrant la commande suivante:

.. sourcecode:: bash

  kpsewhich -var-value TEXMFHOME

et ce **quelque soit votre système d'exploitation** (ou la distribution installée).
Créez les sous dossiers ``tex`` puis ``latex`` si ce n'est pas le cas.
Notez que l'utilisation de ``texhash`` n'est pas nécessaire.
