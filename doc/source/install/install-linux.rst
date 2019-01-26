=======================
Installation sous Linux
=======================

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.


.. note::

    - Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.
    - Il est impératif que la locale ``fr_FR.UTF-8`` soit installée sur votre distribution.
    - Si vous voulez savoir ce qui se cache derrière une commande ``make``, ouvrez le fichier nommé ``Makefile`` présent à la racine du projet.
    - L'installation automatique des packages a été testée sour Ubuntu, Debian, Fedora et Archlinux. Si vous utilisez une autre distribution, essayez d'installer la liste de packages `située ici <#composant-packages>`_.
    - Si une erreur s'est glissée dans la doc, ou si la doc a glissé vers l'obscolescence, ouvrez `un ticket sur notre repo github <https://github.com/zestedesavoir/zds-site/issues/new>`_
    - Si malgré tout vous ne parvenez pas à installer ZdS, n'hésitez pas à ouvrir `un sujet sur le forum <https://zestedesavoir.com/forums/sujet/nouveau/?forum=2>`_


Après avoir cloné, installer ZdS sous Linux est relativement simple. En effet, il suffit de lancer la commande suivante (qui se chargera d'installer ce qui est nécessaire, plus d'infos ci-dessous):

.. sourcecode:: bash

    make install-linux

Notez que si vous voulez installer une version complète (avec une version locale  `de LaTeX <#composant-tex-local-et-latex-template>`_ et `de Elasticsearch <#composant-elastic-local>`_, plus d'infos ci-dessous), utilisez plutôt

.. sourcecode:: bash

    make install-linux-full

Une fois que c'est fait, vous pouvez directement lancer votre instance à l'aide des commandes suivantes:

.. sourcecode:: bash

    source zdsenv/bin/activate # activer le virtualenv
    make zmd-start # démarrer zmarkdown
    make run-back # démarer le serveur django


Stoppez le serveur à l'aide de ctrl+c. Pour sortir de votre environnement, tapez ``deactivate``.

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.

Plus d'informations
-------------------

La commande ``make install-linux[-full]`` appelle en fait le script ``scripts/install_zds.sh`` avec ``+base`` (ou ``+full``).
Ce script est concu de manière modulaire pour installer des composants de ZdS (sous Linux) à l'aide de ``scripts/install_zds.sh +back +front [...]``, le ``+`` indiquant qu'on souhaite **installer** un composant (ici ``front`` et ``back``).
Les différents composants sont listé ci-dessous.


Composants ``base``
===================

Équivalent à  ``+packages +virtualenv +node +back +front +zmd +data`` (plus de détails ci-dessous).
Notez que si vous ne souhaitez pas un de ces compsants, vous pouvez utiliser la syntaxe ``scripts/install_zds.sh +base -machin -bidule``, le ``-`` indquant qu'on ne souhaite pas installer un composant.

Composants ``full``
===================

Équivalent à ``+base +elastic-local +tex-local +latex-template`` (plus de détails ci-dessous).
De même que pour `base <#composants-base>`_, vous pouvez agrémenter de ``-composant`` pour ne pas installer un composant donné.


Composant ``packages``
======================

Installe les packages nécessaire à l'utilisation et au dévellopement de Zeste de Savoir à l'aide du gestionnaire de paquet de votre distribution (détecte et fonctionne pour Ubuntu, Debian, Fedora et Archlinux).

La liste des packages vous est donnée ci-dessous (pour Debian), si vous utilisez une distribution différente, le nom des paquets à installer devrait être fort semblable, n'hésitez dès lors pas à employer la fonction "recherche" de votre gestionnaire de paquet préféré.

- python3 et dérivés : ``python3-dev python3-setuptools python3-pip python3-venv`` ;
- realpath : ``realpath`` (se trouve dans le package ``coreutils`` sous Ubuntu 18.04) ;
- gcc et make (pour compilation et utilisation du  ``Makefile``): ``apt-get install build-essential`` ;
- Pour ``lxml``: ``libxml2-dev`` ;
- ``libxlst-dev`` (peut être appelée ``libxlst1-dev`` sur certains OS comme Ubuntu) ;
- ``libz-dev`` (peut être ``libz1g-dev`` sur système 64bits) ;
- libffi : ``apt-get install libffi-dev`` ;
- Dépendances de `Pillow <https://pillow.readthedocs.io/en/3.1.x/index.html>`_ : ``libjpeg62-turbo libjpeg62-turbo-dev libfreetype6 libfreetype6-dev`` (peut être appelée ``libjpeg8`` et ``libjpeg8-dev``) ;
- Dépendances de la *template* LaTeX: ``xzdec``, ``librsvg2-bin`` et ``imagemagick``.

Composant ``virtualenv``
========================

Installe le *virtualenv* qui est un environement python cloisonné prévu pour ne pas interférer avec d'autres installation de python (`plus d'infos ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_).
Ce que fait ce composant est tout simplement:

.. sourcecode:: bash

    python3 -m venv $ZDS_VENV

Le nom du *virtualenv* est donc controlé par la variable d'environement ``ZDS_VENV`` (dont la valeur est par défaut ``zdsenv``).

Composant ``node``
==================

Installe ``nvm`` et l'utilise pour installer ``node``, puis ``yarn``.
Ajoute ensuite un ``.nvmrc`` dans le dossier et ajoute ``node use`` au script d'activation du *virtualenv* (pour qu'il soit automatiquement utilisé au chargement).
La version de node installée est controlée par la variable d'environement ``ZDS_NODE_VERSION`` (dont la valeur est par défaut ``10.8.0``).

Si vous ne souhaitez pas utiliser ce composant, il vous faut tout de même installer les outils du front-end manuellement. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Composant ``back``
==================

Installe les packages python nécessaire au bon fonctionnement et au dévelopement de ZdS, puis installe les migrations.
Strictement équivalent au commande suivantes:

.. sourcecode:: bash

    make install-back # Dépendances Python
    make migrate-db # Cf. "migrate" de Django

Composant ``front``
===================

Installe les dépendances du front-end en utilisant ``yarn``, puis *build* le front-end.
Strictement équivalent au commande suivantes:

.. sourcecode:: bash

    rm -R node_modules
    make install-front
    make build-front

Si vous ne souhaitez pas utiliser ce composant, il vous faut tout de même installer les outils du front-end manuellement. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Composant ``zmd``
=================

Installe le serveur *zmarkdown*, nécessaire au bon fonctionement du site.
Strictement équivalent à la commande suivantes:

.. sourcecode:: bash

    make zmd-install

Si vous ne souhaitez pas utiliser ce composant, il vous faut tout de même installer zmarkdown manuellement.
Pour cela, rendez-vous sur `la documentation dédiée <extra-zmd.html>`_.

Composant ``data``
==================

Installe le jeu de données de test de ZdS, pour le dévelopement.
Strictement équivalent à la commande suivantes:

.. sourcecode:: bash

    make generate-fixtures

Plus d'info sur cette fonctionalité `sur la page dédiée <../utils/fixture_loaders.html>`_.

Composant ``elastic-local``
===========================

Installe une version **locale** d'Elasticsearch dans un dossier ``.local`` situé dans le dossier de ZdS.
La commande ``elasticsearch`` est ensuite ajoutée dans le *virtualenv*, de telle sorte à ce que ce soit cette version locale qui soit utilisée.
La version d'Elasticsearch installée est controlée par la variable d'environement ``ZDS_ELASTIC_VERSION`` (dont la valeur est par défaut ``5.5.2``).

Notez que vous pouvez choisir d'installer Elasticsearch manuellement, `comme décrit ici <./extra-install-es.html#sous-linux>`_.

Composant ``tex-local`` et ``latex-template``
=============================================

Ces composants s'assurent que votre instance locale peut utiliser LaTeX (en fait LuaLaTeX) pour générer des PDFs des contenus.

Le composant ``tex-local`` installe une version **locale** (et allégée) de `Tex Live <https://tug.org/texlive/>`_ dans un dossier ``.local`` situé dans le dossier de ZdS.
Elle s'ocuppe également d'installer les polices d'écritures nécessaire au bon fonctionement de la *template* dans votre ``$HOME``.
Les commandes spécifiques à TeX sont ensuite ajoutées dans le *virtualenv*, de telle sorte à ce que ce soit cette version locale qui soit utilisée le cas échéant.

Indépendament, le composant composant ``latex-template`` installe (ou met à jour) la template LaTeX (nécessaire à la génération des PDFs) dans le dossier ``TEXMFHOME/tex/latex``.
Ce composant peut donc être utilisé même si vous avez installé TeX Live par d'autres moyens.

Ces deux composants reposent sur des scripts situés dans `le dépot du template LaTeX <https://github.com/zestedesavoir/latex-template>`_.
Le dépot installé est controlé par la variable d'environement ``ZDS_LATEX_REPO`` (dont la valeur est l'url actuelle du dépôt sur Github).

.. note::

    Notez qu'une fois TeX Live installé, le composant ``tex-local`` peut être réutilisé pour mettre à jour les packages spécifiques à la *template* LaTeX.
    Si vous souhaitez réinstaller totalement TeX live, supprimez le dossier ``.local/texlive``.

Vous pouvez néanmoins choisir d'installer manuellement ces outils, `tel que décrit ici <extra-install-latex.html>`_.

