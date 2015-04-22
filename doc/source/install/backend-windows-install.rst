====================================
Installation du backend sous Windows
====================================

Pour installer une version locale de ZdS sur Windows, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Prérequis
=========

- Téléchargez et installez les outils suivants :
    - `PowerShell 3.0+ <http://www.microsoft.com/fr-fr/download/details.aspx?id=40855>`_
    - `Git <http://git-scm.com/download/win>`_ (Git pour Eclipse ne suffit pas ; associez les .sh)
    - `gettext <https://www.gnu.org/software/gettext/>`_
- `Téléchargez et installez Python 3.4 <https://www.python.org/downloads/release/python-34/>`_
- Installez setuptools : Démarrez `Powershell <http://fr.wikipedia.org/wiki/Windows_PowerShell>`_ **en mode administrateur** et lancez la commande suivante : ``(Invoke-WebRequest https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py).Content | python -``
- Redémarrez Powershell
- Installez pip : ``easy_install pip``
- Installez tox : ``pip install tox``
- Désactivez la sécurité sur les script powershell ``Set-ExecutionPolicy RemoteSigned``
- Installez Virtualenv avec les commandes suivante : 
    - ``pip install virtualenv``
    - ``pip install virtualenvwrapper-powershell``
- Créez votre workspace dédié à ZdS
    - ``set $env:WORKON_HOME``
    - ``mkdir '~\.virtualenvs'``
    - ``Import-Module virtualenvwrapper``
    - ``New-VirtualEnvironment zdsenv --no-site-packages``
- Cloner le dépot git *via la console git* (et pas via powershell) windows: ``git clone https://github.com/zestedesavoir/zds-site.git``

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
- Pour redémarrer virtualenv les fois suivantes : ``~\.virtualenvs\zdsenv\Scripts\activate.ps1``

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez `MikTex <http://miktex.org/download>`_
- Téléchargez et installez `Pandoc <https://github.com/jgm/pandoc/releases>`_
