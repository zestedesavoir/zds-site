=========================
Installation sous Windows
=========================

Pour installer une version locale de ZdS sur Windows, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Il est conseillé de lancer à chaque fois PowerShell en administrateur pour les étapes suivantes et choisissez un répertoire pour le zds par exemple :

.. sourcecode:: bat

    cd C:\dev\zestedesavoir


.. Attention::

    Il est fortement recommandé (pour des raisons de compatibilité), que tous les programmes à installer soient en 32 bits ou en 64 bits. Il est conseillé de ne pas mélanger les deux.


Cas numéro 1 : windows 10 et sous-système linux
===============================================

- Utilisez `le sous-système linux<https://docs.microsoft.com/en-us/windows/wsl/install-win10>`
- (exemple pour le sous système ubuntu)
    .. sourcecode:: bash

        sudo apt install build-essential git
        git clone https://github.com/<votre-pseudo>/zds-site
        cd zds-site
        ./scripts/install_zds.sh -packages ubuntu

Cas numéro 2 : fonctionnement sur windows lui-même
==================================================

Installation automatique
---------------------

Commencez par télécharger et installer Python <https://www.python.org/>`. Installez PowerShell et autorisez l'exécution des scripts powershell en copîant cette ligne de code dans votre console : `powershell -Verb RunAs -ArgumentList "Set-ExecutionPolicy RemoteSigned" -WindowStyle Hidden -Wait`.

Ensuite, ouvrez la console de Windows et faites :

.. sourcecode:: batch

    cd /ton/path/zds-site/
    powershell .\scripts\win\install_zds.ps1 +full


Une fois l'installation fini, utilisez la **console PowerShell** et chargez l'environnement virtuel de votre espace de développement avec :

.. sourcecode:: powershell

    . .\zdsenv\Scripts\activate.ps1

Vous devriez obtenir :

.. sourcecode:: bat

    (zdsenv)PS C:\dev\zestedesavoir\

Vous pouvez finalement lancer ZdS:

- Démarrer ZMD : `pm2 start --name=zmarkdown -f zmd/node_modules/zmarkdown/server/index.js -i 1`
- Démarrer Django : `python manage.py runserver`


Installation manuelle
---------------------

- Téléchargez `zlib <http://gnuwin32.sourceforge.net/downlinks/zlib.php>`_ (prérequis pour la bibliothèque ``Pillow``)
- Téléchargez et installez les outils suivants :
    - `PowerShell 3.0+ <http://www.microsoft.com/fr-fr/download/details.aspx?id=40855>`_. Uniquement pour les PC tournant sous Windows 7 ou antérieur (installé par défaut avec Windows depuis).
    - `Git <http://git-scm.com/download/win>`_ (Git pour Eclipse ne suffit pas ; associez les .sh).
    - `gettext <https://mlocati.github.io/articles/gettext-iconv-windows.html>`_.
- `Téléchargez et installez Python 3.6 <https://www.python.org/downloads/release/python-368/>`_.
- Installez setuptools : Démarrez Powershell en mode administrateur et lancez la commande suivante : ``Set-ExecutionPolicy RemoteSigned``
- Installez Virtualenv avec les commandes suivante :
    - ``pip install virtualenv``
- Clonez le dépot git *via la console git** (ou bien avec powershell qui ne doit pas être exécuté en tant qu'administrateur): ``git clone https://github.com/zestedesavoir/zds-site.git``
- Créez votre workspace dédié à ZdS (mode administrateur obligatoire).
    - se placer dans le dossier du dépôt cloné (``zds-site``)
    - tapez ``virtualenv zdsenv`` (il va alors créer l'environnement virtuel ``zdenv``)
    - Activez l'environnement en exécutant le fichier ``zdsenv/Scripts/activate.ps1``

(?) Si vous avez ``(zdsenv)`` à gauche de la zone de saisie, c'est que vous êtes dans l'environnement *zdsenv*.

Pour redémarrer virtualenv les fois suivantes : exécutez à nouveau le fichier ``zdsenv/Scripts/activate.ps1``.

.. sourcecode:: bat

    (zdsenv)PS C:\dev\zestedesavoir\

Lancez par la suite ``pip install --upgrade -r requirements-dev.txt``.

Si l'erreur suivante apparaît :

.. error::
    Unable to find vcvarsall.bat

Installez le compilateur Visual C++ pour Python disponible `ici  <https://www.microsoft.com/en-us/download/confirmation.aspx?id=44266>`_.

Pour que la modification soit effective, relancer une nouvelle fenêtre powershell.

Les virtualenvs et pycharm
--------------------------

Avec PyCharm (Pour avoir une license Pro contactez le directeur technique (DTC)) vous pouvez gérer les virtualenv de manière bien plus performante qu'avec la commande powershell de base.
Bien que le wrapper doive être installé comme dit au dessus, PyCharm vous offre une interface plus maniable.
Ouvrez le projet dans PyCharm, puis allez dans Fichier(File)->Settings
Dans "Project interpreter" sélectionnez la version "Python 3.4" que vous avez installée. Cliquez alors sur la roue dentée puis "Create virtualenv". Vous pourrez alors sélectionner le dossier dans lequel
se trouve le virtualenv et son accessibilité par PyCharm. PyCharm vous notifiera alors que vous n'avez pas toutes les dépendances et vous proposera de les installer.

.. attention::
    Par défaut PyCharm ne va pas chercher les dépendances dans requirements-dev.txt.
    Vous pouvez installer les dépendances depuis PowerShell ou bien aller dans l'onglet Tools des settings puis dans la partie "Python Integration" pour y changer temporairement le chemin vers le fichier de dépendances.


Installation des outils front-end et de zmarkdown
=================================================

Il vous faut installer les outils du front-end.
Pour cela, rendez-vous sur `la documentation dédiée <extra-install-frontend.html>`_.
Ensuite, `installez zmarkdown <extra-zmd.html>`_

Suite et fin de l'installation
==============================

Dans la console PowerShell via l'environnement zdsenv installez les dépendances:

- ``pip install --upgrade -r requirements-dev.txt``
- ``python .\manage.py migrate`` ;
- ``python .\manage.py loaddata (dir .\fixtures\*.yaml)``, puis ``python .\manage.py load_factory_data .\fixtures\advanced\aide_tuto_media.yaml``, afin de créer `le jeu de données utile au développement <../utils/fixture_loaders.html>`_.

On peut finalement lancer ZdS:

- ``cd zmd/node_modules/zmarkdown && npm run server`` `pour zmarkdown <extra-zmd.html#utilisation>`_ ;
- ``python manage.py runserver``


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Elasticsearch:

- `Installez Elasticsearch <extra-install-es.html>`_ ;
- `Installez LaTeX <extra-install-latex.html>`_.

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
