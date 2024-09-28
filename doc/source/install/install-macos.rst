=======================
Installation sous macOS
=======================

.. Attention::

  Il y a moins  de contributeurs·trices sur macOS que sur d’autres plateformes.
  Il se peut que l’installation et les tests unitaires fonctionnent correctement,
  partiellement ou pas du tout. Bref, en cas de problème n’hésitez pas à venir
  demander de l’aide sur le `forum des Devs’ de Zeste de Savoir
  <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ !

  Les instructions ci-dessous ont été testées avec succès sur un MacBook Pro
  fin-2021, avec processeur M1 Pro, sous macOS 12 (Monterey) et 13 (Ventura).

Pour installer une version locale de ZdS sur macOS, veuillez suivre les
instructions suivantes. Si une commande ne passe pas, essayez de savoir pourquoi
avant de continuer.

macOS étant un système UNIX proche de Linux, l’installation fonctionne quasiment
comme pour cet OS, à quelques détails près. La principale différence est que
macOS étant basé sur BSD, il faut remplacer les outils BSD par ceux de GNU (les
``gnu-coreutils``, utilisés sous Linux), et avec lesquels ``zds-site`` est conçu.

.. note::

  Les instructions ci-dessous sont écrites pour macOS, mais il se peut que leur
  philosophie (utiliser les ``gnu-coreutils`` au lieu de ceux de BSD) permette
  d’installer ``zds-site`` sur un système \*BSD.


Pré-requis
==========

.. admonition:: Avis aux utilisateurs·trices avancé·es

  Ces instructions expliquent comment installer XCode, Homebrew, Python, pip, et
  les utilitaires GNU, sur macOS. Si vous avez déjà :

  - une installation fonctionnelle de Homebrew et de Python 3.8+ ;
  - configuré votre terminal pour utiliser les utilitaires GNU à la place de
    ceux de BSD (avec `linuxify <https://github.com/darksonic37/linuxify#install>`_,
    par exemple) ;

  alors vous pouvez `passer à la section suivante <#dependances-systeme>`_
  concernant l’installation de ``zds-site``.

XCode
-----

Pour installer ou lancer ``zds-site`` sur macOS, vous devrez utiliser un
terminal pour pouvoir y entrer des commandes servant à installer ou lancer
le site et ses composants annexes. `macOS intègre un terminal nativement
<https://support.apple.com/fr-fr/guide/terminal/apd5265185d-f365-44cb-8b09-71a064a42125/mac>`_,
que vous pouvez utiliser.

Pour utiliser complètement le terminal sous macOS, vous devez installer quelques
outils supplémentaires qui ne sont pas installés de base avec macOS. Depuis
votre terminal, exécutez cette commande pour les installer.

.. sourcecode:: bash

  xcode-select --install

Homebrew
--------

Vous aurez ensuite besoin d’**Homebrew**, un système permettant de télécharger et
d’installer des logiciels sous macOS depuis la ligne de commande, et de les
mettre à jour. Nous nous en servirons pour installer Python (si nécessaire) et
les dépendances de ``zds-site``.

`Les instructions d’installation d’Homebrew sont sur leur site web <http://brew.sh/>`_.

Python 3
--------

``zds-site`` dépend d’une version récente de Python 3. Sous macOS Ventura et plus
récent (macOS 13+), Python 3 est installé avec XCode, qu’on a installé plus haut.
Pour vérifier, exécutez la commande suivante :

.. sourcecode:: bash

  python --version

Si vous obtenez une version inférieure à Python 3.9 (et notamment si vous voyez
``Python 2.7``), il vous faudra installer une version récente de Python avec
Homebrew. Sinon, vous pouvez utiliser la version intégrée avec macOS de Python,
mais vous devrez installer ``pip``.

Si votre version de Python est trop vieille
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Il vous faut installer Python avec Homebrew. Exécutez dans un terminal :

.. sourcecode:: bash

  brew install python

Puis revérifiez la version de Python avec ``python --version``. Si elle n’a pas
changé, tentez de redémarrer votre terminal.

Si vous gardez la version native de Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Si vous avez décidé de garder la version native de Python, si elle est assez récente,
vous allez quand même devoir installer ``pip``, un logiciel compagnon de Python
servant à installer des bibliothèques externes en Python — des extensions
permettant d’augmenter ses possibilités facilement.

Pour vérifier que vous disposez de ``pip``, exécutez l’une de ces commandes :

.. sourcecode:: bash

  pip --version           # ou
  pip3 --version          # ou
  python -m pip --version

Vous devriez obtenir un numéro de version de pip et de Python, comme cela :

.. sourcecode:: bash

  $ pip --version  # ou une des autres commandes
  pip 22.3.1 from /opt/homebrew/lib/python3.10/site-packages/pip (python 3.10)

Si ces commandes retournent toutes une erreur, et non un numéro de version,
vous devez installer ``pip``. `Les instructions d’installation sont sur le site
web de pip. <https://pip.pypa.io/en/stable/installation/>`_

Utilitaires GNU/Linux au lieu de BSD
------------------------------------

``zds-site`` est conçu pour fonctionner avec les utilitaires de Linux (les
``gnu-coreutils``), différents des utilitaires natifs de \*BSD (et donc de macOS,
qui en est un lointain descendant).

Le plus simple est le projet ``linuxify``, qui installe toutes les versions GNU
de divers logiciels avec Homebrew. Par défaut, ces versions viennent préfixées,
pour ne pas entrer en conflit avec les versions du système. En pratique, ce n’est
pas un problème d’utiliser dans votre environnement local les versions de GNU,
donc vous pouvez utiliser en permanence ces versions à la place de celles de BSD.

Dans le doute, remplacez en permanence par les versions de GNU : c’est sans impact
négatif et ça permet à ``zds-site`` de fonctionner sans manipulation particulière.

`Commencez par installer linuxify <https://github.com/darksonic37/linuxify#install>`_,
tel que précisé sur leur site. Si vous avez une erreur disant ``command not found: git``,
exécutez dans votre terminal la commande ``brew install git``.

Lorsqu’il vous demande *Do you want to change your shell to the latest bash*,
répondez non (``n``).

Ensuite, si vous choisissez de remplacer en permanence les utilitaires BSD par
ceux de GNU, exécutez la commande suivante pour automatiquement utiliser les
utilitaires GNU quand vous utilisez votre terminal, puis redémarrez votre terminal.

.. sourcecode:: bash

  echo ". ~/.linuxify" >> ~/.zshrc

Si vous choisissez de ne **pas** le faire, alors il vous faudra exécuter cette
commande dans *chaque* terminal où vous exécuterez des commandes d’installation
ou de mise à jour de ``zds-site`` (une fois par terminal, pas besoin de la
ré-exécuter à chaque fois) :

.. sourcecode:: bash

  . ~/.linuxify


Dépendances système
===================

Le script d’installation n’installant pas encore les paquets automatiquement sur
macOS, vous devez le faire à la main, via Homebrew. Exécutez la commande
suivante pour tout installer.

.. sourcecode:: bash

  brew install curl gettext cairo


Une fois les pré-requis terminés, vous pouvez vous lancer dans l‘installation
de l’environnement de ``zds-site``.


Installation de ``zds-site``
============================

Commencez par cloner le dépôt de ``zds-site``, ou idéalement, votre fork sur
lequel vous travaillerez avant d’envoyer des *Pull-Requests*.

.. sourcecode:: bash

  git clone git@github.com:VOTRE-PSEUDO-GITHUB/zds-site.git
  cd zds-site

``zds-site`` peut s’installer de deux façons :

- une version minimale, qui ne contient que le site lui-même, mais pas le moteur
  de recherche ni le système d’export des PDF ;
- une version complète, qui contient tout, et qui est aussi plus lourde à
  installer.

.. Attention::

  La version complète **ne peut être automatiquement installée pour le moment**
  car l’installeur télécharge une version de Typesense (le moteur de recherche) spécifique
  à Linux.

  Le système de génération et d’export des PDF devrait fonctionner normalement.

  La version minimale a été testée avec succès.

.. seealso::

  - `Installation de Typesense <extra-install-search-engine.html>`_ ;
  - `installation de LaTeX <extra-install-latex.html>`_.

Pour installer la version minimale, exécutez depuis la racine du dépôt que vous
venez de cloner :

.. sourcecode:: bash

  ./scripts/install_zds.sh +base -packages

Si vous voulez la version complète :

.. sourcecode:: bash

  ./scripts/install_zds.sh +full -packages

.. note::

  L’option ``-packages`` désactive l’installation automatique des dépendances
  système, qui n’est pour le moment supportée que sous Linux.

.. note::

  Vous pouvez relire le script avant de l’exécuter pour savoir ce qu’il fait.
  Mais dans l’idée, ce script va :

  - installer ``virtualenv`` (via ``pip``), un logiciel Python permettant de
    créer des environnements virtuels cloisonnés en Python ;
  - créer un environnement virtuel dans le sous-dossier ``zdsenv`` ;
  - installer dans votre dossier utilisateur le logiciel ``nvm`` (*Node Versions
    Manager*), un outil permettant d’installer différentes versions de NodeJS ;
  - installer la bonne version de NodeJS localement (uniquement pour ``zds-site``)
    et intégrer le chargement de la cette bonne version à l’environnement virtuel ;
  - installer les dépendances de ``zds-site`` dans l’environnement virtuel ;
  - installer ``zmarkdown``, le moteur de rendu Markdown utilisé par ``zds-site`` ;
  - installer les dépendances du *front-end* avec ``npm`` puis compiler le
    *font-end* ;
  - créer la base de données utilisée par ``zds-site`` (avec SQLite) et la
    remplir de données de test ;
  - intégrer au dépôt local un *pre-commit hook* `vérifiant que le code Python
    est correctement formaté à chaque commit <../utils/git-pre-hook.html>`_
    (et le formatant le cas échéant).

  Si vous installez la version complète, le script va, en plus :

  - installer Typesense dans le dossier ``zds-site/.local/typesense`` ;
  - installer TeXLive (permettant de compiler du LaTeX en PDF, utilisé pour les
    exports PDF) dans le dossier ``zds-site/.local/texlive`` ;
  - cloner le dépôt contenant le modèle LaTeX utilisé par l’export PDF dans le
    dossier ``zds-site/latex-template``.


Lancement de ``zds-site``
=========================

Une fois dans votre environnement Python et toutes les dépendances installées,
lançons ZdS.

Il faut d’abord lancer ``zmarkdown``, le moteur de rendu Markdown utilisé par
Zeste de Savoir. Ce moteur fonctionne sur un modèle client-serveur : ``zds-site``
envoie une requête HTTP (en local) pour obtenir le rendu d’un document Markdown
en HTML, ePub, ou LaTeX. Il faut donc démarrer le serveur ``zmarkdown`` en
arrière-plan.

Ensuite, on démarre ``zds-site``.

.. sourcecode:: bash

  # Depuis la racine du dépôt zds-site
  make zmd-start
  make run

Le démarrage de ``zds-site`` entraîne celui du *backend* Python dans un mode
optimisé pour le développement. Notamment, le cache est totalement désactivé
et des outils de débogage rendent disponible plein d’informations sur chaque
page, les données techniques envoyées (paramètres de templates, …) et les
requêtes SQL envoyées. Ces outils sont pratiques mais ils peuvent être lourds.
Si vous avez une machine peu puissante et que vous voulez une version plus légère,
mais sans tous ces outils de développement, vous pouvez démarrer une version
plus légère de ``zds-site`` ainsi.

.. sourcecode:: bash

  make run-fast

Ces deux façons de lancer ``zds-site`` lancent aussi la compilation automatique
à la moindre modification des fichiers du *front-end* (SCSS, JS, etc.). Si vous
voulez également désactiver cela, car vous ne travaillez pas sur le *front-end*
et/ou que vous voulez une version plus légère du site, vous pouvez ne lancer que
le *back-end* :

.. sourcecode:: bash

  make run-back       # ou (cf. plus haut)
  make run-back-fast

Pour lister toutes les options disponibles, exécutez simplement, sans argument :

.. sourcecode:: bash

  make

Données de test
===============

L’installeur a créé pour nous le `jeu de données utile au développement
<../utils/fixture_loaders.html>`_. Si pour une raison ou pour une autre, vous
voulez repartir de zéro en écrasant toutes les données de votre installation
locale, vous pouvez le faire.

.. warning::

  Cette commande **supprime totalement votre base de données, ainsi que tous les
  contenus que vous avez pu créer, sur votre instance locale**, puis recrée des
  données de test aléatoires à partir de zéro.

  **Il n’est pas possible d’annuler cette opération.**

.. sourcecode:: bash

    make new-db

Mettre à jour votre instance locale
===================================

Pour rapidement mettre votre instance locale à jour, par exemple pour tester une
*Pull-Request* ou si vous vous êtes mis à jour depuis le dépôt principal, lancez :

.. sourcecode:: bash

  make update

Cette commande va mettre à jour le *back-end* et le *front-end*, puis migrer la
base de données (si nécessaire) et recompiler le *front-end*.
