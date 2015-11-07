====================================
Installation du backend sous Windows
====================================

-----------

.. Attention::

    Cette partie de la documentation n'est probablement pas à jour faute de contributeur utilisant Windows. Il se peut que l'installation et les tests unitaires fonctionnent correctement, partiellement ou pas du tout. Bref, en cas de problème n'hésitez pas à venir demander de l'aide sur le `forum des Devs' de Zeste de Savoir <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ !

-----------


Pour installer une version locale de ZdS sur Windows, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Il est conseillé de lancer à chaque fois PowerShell en administrateur pour les étapes suivantes et choisissez un répertoire pour le zds par exemple :

.. sourcecode:: none

    cd C:\dev\zestedesavoir

Prérequis
=========


- Téléchargez et installez les outils suivants :
    - `PowerShell 3.0+ <http://www.microsoft.com/fr-fr/download/details.aspx?id=40855>`_.
    - `Git <http://git-scm.com/download/win>`_ (Git pour Eclipse ne suffit pas ; associez les .sh).
    - `gettext <https://www.gnu.org/software/gettext/>`_.
- `Téléchargez et installez Python 2.7 <https://www.python.org/download/releases/2.7/>`_.
- Installez setuptools : Démarrez Powershell et lancez la commande suivante : ``(Invoke-WebRequest https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py).Content | python -``
- Décompressez l'archive ``setuptools-*XX.X.X*.zip``.
- Avec la commande ``cd setuptools-XX.X.X``, ouvrer le répertoire possèdant *easy_install.py*.
- Installez pip et tox : ``python easy_install.py pip tox``.
- Vous devriez avoir un nouveau répertoire ``C:\Python27\Scripts``, rajoutez le dans le *PATH, la variable d'environnement*.
- Réinstallez easyinstall : ``python easy_install.py easyinstall``, ça vous permettra de l'utiliser partout, (supprimez l'ancien package).
- Redémarrez Powershell (pour recharger *la variable d'environnement PATH*).
- Installez Virtualenv avec les commandes suivante :
    - ``pip install virtualenv``
    - ``pip install virtualenvwrapper-powershell``
- Désactivez la sécurité sur les script powershell (mode administrateur obligatoire) : ``Set-ExecutionPolicy RemoteSigned``, pour autoriser ``Import-Module``.
- Créez votre workspace dédié à ZdS (mode administrateur obligatoire).
    - ``set $env:WORKON_HOME``
    - ``Import-Module virtualenvwrapper``, *la console PowerShell pourrait hurler à cette commande, mais normalement ça passe, en cas de deuxième essai vous ne devriez plus avoir d'erreur*.
    - ``New-VirtualEnvironment zdsenv --no-site-packages``
- Clonez le dépot git *via la console git* (et pas via powershell) windows: ``git clone https://github.com/zestedesavoir/zds-site.git``

(?) Si vous avez ``(zdsenv)`` à gauche de la zone de saisie, c'est que vous êtes dans l'environnement *zdsenv*.

.. sourcecode:: none

    (zdsenv)PS C:\dev\zestedesavoir\

Pour redémarrer virtualenv les fois suivantes : ``workon zdsenv``.

Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.

Suite de l'installation
=======================

- Dans la console PowerShell via l'environnement zdsenv installez les dépendances.
    - ``easy_install lxml``
    - ``pip install -r requirements.txt -r requirements-dev.txt``
    - ``python manage.py migrate``
    - ``python manage.py runserver``

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez `MikTex <http://miktex.org/download>`_
- Téléchargez et installez `Pandoc <https://github.com/jgm/pandoc/releases>`_
