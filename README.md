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
- Python 2.7 (avec les fichiers de developpement, les paquets `python-dev` et `python-lxml` sous Debian/Ubuntu)
- Pip
- git

### Installation d'une version locale de ZDS

**NB : si une commande ne marche pas, vérifier pourquoi avant de continuer**

####Installation sur **Windows 7, 8** et plus

- Téléchargez et installez les outils suivants :
    - [PowerShell 3.0+](http://www.microsoft.com/fr-fr/download/details.aspx?id=40855)
    - [Git](http://git-scm.com/download/win) (Git pour Eclipse ne suffit pas ; associez les .sh)
- [Téléchargez et installez Python 2.7](https://www.python.org/download/releases/2.7/)
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

####Sur OS X
Avant de vous lancez dans l'installation de l'environnement de zds, il faut quelques pré-requis :
* Installer [XCode](https://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12) pour pouvoir exécuter des commandes (g)cc.
* Installer [MacPorts](http://www.macports.org/) pour récupérer certains paquets utiles pour l'installation des dépendances de ce projet.

Une fois les pré-requis terminés, vous pouvez vous lancer dans l'installaton de l'environnement de zds :
```
# Installation de virtualenv.
pip install virtualenv
pip install virtualenvwrapper
mkdir ~/.virtualenvs
echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bash_profile && export WORKON_HOME=$HOME/.virtualenvs
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile && source /usr/local/bin/virtualenvwrapper.sh

# Création de votre environnement.
mkvirtualenv zdsenv

# Récupération de la librairie lxml pour python 2.7 via MacPorts.
sudo port install py27-lxml

# Ajout de flags pour compiler avec gcc plutôt que clang lors de l'installation de lxml.
export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments

# Installation de toutes les dépendances.
pip install --upgrade -r requirements.txt
```

Pour relancer votre environnement : `source ~/.virtualenvs/zdsenv/bin/activate`
Pour sortir de votre environnement : `deactive`

####Sur Linux
Faites les commandes suivantes au fur et à mesure (si l'une d'entre elle échoue, resolvez là avant de continuer)

**NB : les commandes suivantes sont génériques et indépendantes de la distribution que vous utilisez. 
**NB2 : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.**

```console
pip install --user --upgrade -r requirements.txt
python manage.py syncdb
python manage.py migrate
python manage.py runserver
```


### Données de test
Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
python manage.py loaddata fixtures/users.yaml
python manage.py loaddata fixtures/forums.yaml
python manage.py loaddata fixtures/topics.yaml
python manage.py loaddata fixtures/mps.yaml
python manage.py loaddata fixtures/categories.yaml
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

Avant de faire une PR, vérifiez que votre code passe tous les tests unitaires et qu'il est compatible PEP-8 (sinon votre Pull Request se verra refusée) en exécutant les commandes suivantes :

```console
python manage.py test
flake8 --exclude=migration,urls.py --max-line-length=120 --ignore=F403
```

Si vous modifiez le modèle, n'oubliez pas de créer les fichiers de migration :

```console
/usr/bin/env python2 manage.py schemamigration app_name --auto
```

Si vous avez une connexion lente et que vous ne voulez travailler que sur une branche précise, vous pouvez toujours ne récupérer que celle-ci :

```
git clone https://github.com/Taluu/ZesteDeSavoir.git --depth 1
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](https://github.com/Taluu/ZesteDeSavoir/blob/dev/doc/deploy.md)
