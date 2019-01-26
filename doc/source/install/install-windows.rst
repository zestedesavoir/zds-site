=========================
Installation sous Windows
=========================

.. Attention::

    Cette partie de la documentation n'est probablement pas à jour faute de contributeur utilisant Windows. Il se peut que l'installation et les tests unitaires fonctionnent correctement, partiellement ou pas du tout. Bref, en cas de problème n'hésitez pas à venir demander de l'aide sur le `forum des Devs' de Zeste de Savoir <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ !
    Notons que le support des SVG est désactivé sur windows.

Pour installer une version locale de ZdS sur Windows, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Il est conseillé de lancer à chaque fois PowerShell en administrateur pour les étapes suivantes et choisissez un répertoire pour le zds par exemple :

.. sourcecode:: none

    cd C:\dev\zestedesavoir


.. Attention::

    Il est fortement recommandé (pour des raisons de compatibilité), que tous les programmes à installer soient en 32 bits ou en 64 bits. Il est conseillé de ne pas mélanger les deux.


Prérequis
=========

- Téléchargez `zlib <http://gnuwin32.sourceforge.net/downlinks/zlib.php>`_ (prérequis pour la bibliothèque ``Pillow``)
- Téléchargez et installez les outils suivants :
    - `PowerShell 3.0+ <http://www.microsoft.com/fr-fr/download/details.aspx?id=40855>`_. Uniquement pour les PC tournant sous Windows 7 ou antérieur (installé par défaut avec Windows depuis).
    - `Git <http://git-scm.com/download/win>`_ (Git pour Eclipse ne suffit pas ; associez les .sh).
    - `gettext <https://www.gnu.org/software/gettext/>`_.
- `Téléchargez et installez Python 3.4 <https://www.python.org/downloads/release/python-344/>`_.
- Installez setuptools : Démarrez Powershell en mode administrateur et lancez la commande suivante : ``(Invoke-WebRequest https://bootstrap.pypa.io/ez_setup.py).Content | python -``
- Décompressez l'archive ``setuptools-*XX.X.X*.zip``.
- Avec la commande ``cd setuptools-XX.X.X``, ouvrez le répertoire possèdant *easy_install.py*.
- Installez pip : ``python easy_install.py pip``.
- Vous devriez avoir un nouveau répertoire ``C:\Python34\Scripts``, rajoutez le dans le *PATH, la variable d'environnement*.
- Réinstallez easyinstall : ``python easy_install.py easyinstall``, ça vous permettra de l'utiliser partout, (supprimez l'ancien package).
- Redémarrez Powershell (pour recharger *la variable d'environnement PATH*).
- Installez Virtualenv avec les commandes suivante :
    - ``pip install virtualenv``
    - ``pip install virtualenvwrapper-powershell``
- Clonez le dépot git *via la console git* (et pas via powershell) windows: ``git clone https://github.com/zestedesavoir/zds-site.git``
- Créez votre workspace dédié à ZdS (mode administrateur obligatoire).
    - se placer dans le dossier du dépôt cloné (``zds-site``)
    - tapez ``virtualenv zdsenv`` (il va alors créer l'environnement virtuel ``zdenv``)
    - Activez l'environnement en exécutant le fichier ``zdsenv/bin/activate.ps1``

(?) Si vous avez ``(zdsenv)`` à gauche de la zone de saisie, c'est que vous êtes dans l'environnement *zdsenv*.

Pour redémarrer virtualenv les fois suivantes : exécutez à nouveau le fichier ``zdsenv/bin/activate.ps1``.

.. sourcecode:: none

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

- ``easy_install lxml`` ;
- ``pip install --upgrade -r requirements-dev.txt``
- Cairo, disponible `ici <https://www.cairographics.org/download>`_ ;
- GTK+ (qui contient les DLL de Cairo) disponible `ici <http://downloads.sourceforge.net/gladewin32/gtk-2.12.9-win32-2.exe>`_ ;
- ``python .\manage.py migrate`` ;
- ``python .\manage.py loaddata (dir .\fixtures\*.yaml)``, puis ``python .\manage.py load_factory_data .\fixtures\advanced\aide_tuto_media.yaml``, afin de créer `le jeu de données utile au dévellopement <../utils/fixture_loaders.html>`_.

On peut finalement lancer ZdS:

- ``cd zmd/node_modules/zmarkdown && npm run server`` `pour zmarkdown <extra-zmd.html#utilisation>`_ ;
- ``python manage.py runserver``


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Elasticsearch:

- `Installez Elasticsearch <extra-install-es.html>`_ ;
- `Installez LaTeX <extra-install-latex.html>`_.

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
