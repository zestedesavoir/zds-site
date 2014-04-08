[![Build Status](https://magnum.travis-ci.com/Taluu/ZesteDeSavoir.png?token=Cu35XY4F6RcYoPgjjcbA)](https://magnum.travis-ci.com/Taluu/ZesteDeSavoir)
[![Licnce GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)

ZesteDeSavoir
=============
Site internet communautaire codé à l'aide du Framework Django 1.5.

* Lien du site : [zestedesavoir](http://www.zestedesavoir.com)
* Lien de teasing : [Teasing](http://zestedesavoir.com/teasing/)

Fonctionnalités implementées
----------------------------

- La gestion du forum
- La gestion des membres
- La gestion des tutoriels
- La gestion des articles
- La gestion des message Privés
- La gestion des galleries d'images

Fonctionnalités à venir
-----------------------
Elles sont reportées essentiellement dans le [bugtraker](https://github.com/Taluu/ZesteDeSavoir/issues?state=open)

Comment démarrer une instance de ZdS ?
--------------------------------------
### Pré-requis
- Python 2.7 (avec les fichiers de developpement, le paquet `python-dev` sous Ubuntu)
- Pip
- git

**NB : les commandes suivantes sont génériques et indépendantes de la distribution que vous utilisez. Si votre distribution propose Python2 par defaut (comme Ubuntu), les commandes `/usr/bin/env python2` peuvent être remplacées par `python` tout simplement.**

### Installation d'une version locale de ZDS

**NB : si une commande ne marche pas, vérifier pourquoi avant de continuer**

####Installation sur **Windows 7, 8** et plus

- Téléchargez et installez les outils suivants :
    - [PowerShell 3.0+](http://www.microsoft.com/fr-fr/download/details.aspx?id=40855)
    - [MinGW](http://sourceforge.net/projects/mingw/files/latest/download)
    - [Git](http://git-scm.com/download/win) (Git pour Eclipse ne suffit pas ; associez les .sh)
- [Téléchargez et installez Python 2.7](https://www.python.org/ftp/python/2.7.5/python-2.7.5.msi)
- Installez setuptools : Démarrez [Powershell](http://fr.wikipedia.org/wiki/Windows_PowerShell) **en mode administrateur** et lancez la commande suivante : `(Invoke-WebRequest https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py).Content | python -`
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
- Cloner le dépot git *via la console git* (et pas via powershell) windows: `git clone https://github.com/Taluu/ZesteDeSavoir.git`
- Dans la console PowerShell via l'environnement zdsenv installez les dépendances.
    - `easy_install lxml`
    - `pip install -r requirements.txt`
    - `cd scripts`
    - `./UseUpdatedWinGitPython.sh`
    - `./UseUpdatedWinZMarkdown.sh`
    - `cd ..`
    - `python manage.py syncdb`
    - `python manage.py migrate`
    - `python manage.py runserver`
- Pour redémarrer virtualenv les fois suivantes : `~\.virtualenvs\zdsenv\Scripts\activate.ps1` 

####Sur Linux
Faites les commandes suivantes au fur et à mesure (si l'une d'entre elle échoue, resolvez là avant de continuer)

```console
pip install --user -r requirements.txt
cd scripts && sudo ./UseUpdatedGitPython.sh && cd ..
cd scripts && sudo ./UseUpdatedPythonMarkdownVersion.sh && cd ..
/usr/bin/env python2 manage.py syncdb
/usr/bin/env python2 manage.py migrate
/usr/bin/env python2 manage.py runserver
```


### Données de test
Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
/usr/bin/env python2 manage.py loaddata fixtures/users.yaml
/usr/bin/env python2 manage.py loaddata fixtures/forums.yaml
/usr/bin/env python2 manage.py loaddata fixtures/topics.yaml
/usr/bin/env python2 manage.py loaddata fixtures/mps.yaml
/usr/bin/env python2 manage.py loaddata fixtures/categories.yaml
```

Cela va créer plusieurs entitées :

* 3 utilisateurs (username/password) :
	* user/user : Utilisateur normal
	* staff/staff : Utilisateur avec les droits d'un staff
	* admin/admin : Utilisateur avec les droits d'un staff et d'un admin
* 3 categories
* 11 forums
* 3 topics with one answer
* 1 mp with 3 participants
* 3 catégories et 2 sous-catégories

### Conseil de developpement

Avant de faire une PR, vérifiez que votre code passe tous les tests unitaires en exécutant les commandes suivantes :

```console
python manage.py test zds.member.tests zds.forum.tests zds.tutorial.tests zds.mp.tests
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](https://github.com/Taluu/ZesteDeSavoir/blob/dev/doc/deploy.md)
