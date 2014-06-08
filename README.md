[![Build Status](https://travis-ci.org/zestedesavoir/zds-site.svg?branch=dev)](https://travis-ci.org/zestedesavoir/zds-site)
[![Coverage Status](https://coveralls.io/repos/zestedesavoir/zds-site/badge.png?branch=dev)](https://coveralls.io/r/zestedesavoir/zds-site?branch=dev)
[![Licnce GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)

ZesteDeSavoir
=============
Site internet communautaire codé à l'aide du Framework Django 1.6.

* Lien du site : [zestedesavoir](http://www.zestedesavoir.com)
* Lien de teasing : [Teasing](http://zestedesavoir.com/teasing/)

Fonctionnalités implementées
----------------------------

- La gestion des forums
- La gestion des membres
- La gestion des tutoriels
- La gestion des articles
- La gestion des message Privés
- La gestion des galleries d'images

Fonctionnalités à venir
-----------------------
Elles sont reportées essentiellement dans le [bugtraker](https://github.com/zestedesavoir/zds-site/issues)

Comment démarrer une instance de ZdS ?
--------------------------------------

### Installation d'une version locale de ZdS
- [Intallation sur Windows](doc/install-windows.md)
- [Intallation sur Linux](doc/install-linux.md)
- [Intallation sur OS X](doc/install-os-x.md)

### Mettre à jour votre version locale de ZdS
Après avoir mis à jour votre dépot, vous devez executer les commandes suivantes (depuis la racine de votre projet) pour mettre à jour les dépendances.

```
python manage.py migrate
pip install --upgrade -r requirements.txt
gulp build
```

### Données de test
Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
python manage.py loaddata fixtures/users.yaml fixtures/forums.yaml fixtures/topics.yaml fixtures/mps.yaml fixtures/categories.yaml

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

Avant de faire une PR, vérifiez que votre code passe tous les tests unitaires et qu'il est compatible PEP-8 (sous peine de refus de Pull Request) en exécutant les commandes suivantes :

```console
python manage.py test
gulp test
flake8 --exclude=migrations,urls.py --max-line-length=120 --ignore=F403,E126,E127,E128 zds
```

Si vous modifiez le modèle (les fichiers models.py), n'oubliez pas de créer les fichiers de migration :

```console
python manage.py schemamigration app_name --auto
```

Si vous avez une connexion lente et que vous ne voulez travailler que sur une branche précise, vous pouvez toujours ne récupérer que celle-ci :

```
git clone https://github.com/zestedesavoir/zds-site.git --depth 1
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](doc/deploy.md)



Zeste de Savoir est basé sur un fork de [Progdupeu.pl](http://progdupeu.pl) ([Dépôt Bitbucket](https://bitbucket.org/MicroJoe/progdupeupl/))
