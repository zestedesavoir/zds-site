[![Build Status](https://magnum.travis-ci.com/Taluu/ZesteDeSavoir.png?token=Cu35XY4F6RcYoPgjjcbA)](https://magnum.travis-ci.com/Taluu/ZesteDeSavoir)
[![Licnce GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)

ZesteDeSavoir
=============
Site internet communautaire codé à l'aide du Framework Django 1.6.

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
    - `python manage.py syncdb`
    - `python manage.py migrate`
    - `python manage.py runserver`
- Pour redémarrer virtualenv les fois suivantes : `~\.virtualenvs\zdsenv\Scripts\activate.ps1` 

####Sur Linux


# Installation de virtualenv

virtualenv est un outil python qui permet, comme son nom le laisse deviner, de créer un environnement virtuel "propre" et dépourvu de toute installation de bibliothèques python. C'est idéal si vous ne voulez pas porter des modifications des bibliothèques python au niveau de votre système d'exploitation complet.

Sous linux, nous procéderons ainsi. Commencez par vous connecter sous root puis lancez la commande suivante :

```console
pip install virtualenv
```

Cela installera virtualenv, tout simplement. Par la suite, nous créerons l'environnement virtuel "ZDS" et nous lui attribuerons les droits de l'utilisateur normal (puisque l'environnement sera créé avec root)

```console
virtualenv ZDS
chown user:user ZDS/ -Rf
```

Déconnectez-vous de root, dirigez-vous dans le dossier de l'environnement virtuel et récupérez le dépôt ZesteDeSavoir (attention, ceci peut prendre du temps)

```console
cd ZDS
git clone https://github.com/Taluu/ZesteDeSavoir.git
```

Une fois cela fait, placez-vous dans ZesteDeSavoir et passez sur la branche dev.

```console
cd ZesteDeSavoir
git checkout dev
```

Reconnectez-vous en root et rajouter dans $PATH le chemin des binaires de l'environnement virtuel

```console
PATH=/path/to/ZDS/bin/:$PATH
```

Faîtes l'installation comme une installation normale, toujours sous root :

```console
pip install -r requirements.txt
```

Toutes les dépendances ont été installées pour lancer ZesteDeSavoir.

Déconnectez-vous de root, remettez à jour la variable d'environnement PATH et faîtes les dernières commandes nécessaires avant de démarrer le serveur...

```console
PATH=/path/to/ZDS/bin/:$PATH
python manage.py syncdb
python manage.py migrate
python manage.py loaddata fixtures/*
python manage.py loaddata fixtures/users.yaml
python manage.py loaddata fixtures/forums.yaml
python manage.py loaddata fixtures/topics.yaml
python manage.py loaddata fixtures/mps.yaml
python manage.py loaddata fixtures/categories.yaml
```

Tout devrait fonctionner à présent ! :-)

N'oubliez pas de maintenir la variable d'environnement en conséquence à chaque fois que vous travaillez sur ZesteDeSavoir !


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

Avant de faire une PR, vérifiez que votre code passe tous les tests unitaires en exécutant la suite complète :

```console
python manage.py test
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](https://github.com/Taluu/ZesteDeSavoir/blob/dev/doc/deploy.md)
