#Installation sur **Windows 7, 8** et plus

Pour installer une version locale de ZdS sur Windows, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

- Téléchargez et installez les outils suivants :
    - [PowerShell 3.0+](http://www.microsoft.com/fr-fr/download/details.aspx?id=40855)
    - [Git](http://git-scm.com/download/win) (Git pour Eclipse ne suffit pas ; associez les .sh)
- [Téléchargez et installez Python 2.7](https://www.python.org/download/releases/2.7/)
- Installez setuptools : Démarrez [Powershell](http://fr.wikipedia.org/wiki/Windows_PowerShell) **en mode administrateur** et lancez la commande suivante : `(Invoke-WebRequest https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py).Content | python -`
- Installation de NodeJS, Ruby, Compass, Bower et Gulp, à partir de [la documentation](gulp.md).
- Redémarrez Powershell
- Installez pip : `easy_install pip`
- Désactivez la sécurité sur les script powershell `Set-ExecutionPolicy RemoteSigned`
- Installez Virtualenv avec les commandes suivante : 
    - `pip install virtualenv`
    - `pip install virtualenvwrapper-powershell`
- Créez votre workspace dédié à ZdS
    - `set $env:WORKON_HOME`
    - `mkdir '~\.virtualenvs'`
    - `Import-Module virtualenvwrapper`
    - `New-VirtualEnvironment zdsenv --no-site-packages`
- Cloner le dépot git *via la console git* (et pas via powershell) windows: `git clone https://github.com/zestedesavoir/zds-site.git`
- Dans la console PowerShell via l'environnement zdsenv installez les dépendances.
    - `easy_install lxml`
    - `npm install -g bower gulp`
    - `pip install -r requirements.txt`
    - `npm install`
    - `gulp build`
    - `python manage.py syncdb`
    - `python manage.py migrate`
    - `python manage.py runserver`
- Pour redémarrer virtualenv les fois suivantes : `~\.virtualenvs\zdsenv\Scripts\activate.ps1` 

Pour faire fonctionner ZdS dans son ensemble vous devez installer les outils LateX et Pandoc.

- Téléchagez et installez [MikTex](http://miktex.org/download)
- Téléchargez et installez [Pandoc](https://github.com/jgm/pandoc/releases)