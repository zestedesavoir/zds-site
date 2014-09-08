[![Build Status](https://travis-ci.org/zestedesavoir/zds-site.svg?branch=dev)](https://travis-ci.org/zestedesavoir/zds-site)
[![Coverage Status](https://coveralls.io/repos/zestedesavoir/zds-site/badge.png?branch=dev)](https://coveralls.io/r/zestedesavoir/zds-site?branch=dev)
[![Licence GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)

# Zeste de Savoir

Site internet communautaire codé à l'aide du framework [Django](https://www.djangoproject.com/) 1.6 et de [Python](https://www.djangoproject.com/) 2.7.

* Lien du site : [zestedesavoir](http://www.zestedesavoir.com)

## Fonctionnalités implementées

- Tutoriels
- Articles
- Membres
- Forums
- Messages privés
- Galeries d'images
- Recherche

## Fonctionnalités à venir

Elles sont reportées essentiellement dans le [bugtraker](https://github.com/zestedesavoir/zds-site/issues).

## Comment démarrer une instance de ZdS ?

### Installation d'une version locale de ZdS
- [Intallation sur Windows](doc/install-windows.md)
- [Intallation sur Linux](doc/install-linux.md)
- [Intallation sur OS X](doc/install-os-x.md)
- [Installation de Solr](doc/install-solr.md) pour gérer la recherche

### Mettre à jour votre version locale de ZdS
Après avoir mis à jour votre dépot, vous devez executer les commandes suivantes (depuis la racine de votre projet) pour mettre à jour les dépendances.

```
python manage.py migrate
pip install --upgrade -r requirements.txt
```

### Données de test
Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
python manage.py loaddata fixtures/*.yaml

```

Cela va créer plusieurs entitées :

* 3 utilisateurs (utilisateur/mot de passe) :
	* user/user : Utilisateur normal
	* staff/staff : Utilisateur avec les droits d'un staff
	* admin/admin : Utilisateur avec les droits d'un staff et d'un admin
* 3 catégories
* 11 forums
* 3 sujets avec une réponse
* 1 message privé (MP) avec 3 participants
* 3 catégories et 2 sous-catégories


### Génération de la documentation complète

La documenation de ZdS est générée par Sphinx, et elle doit être mise à jour à chaque modification ou ajout d'une fonctionnalité du site.

Pour générer la documentation rendez vous dans le répertoire `zds-site/doc/sphinx` depuis votre terminal, et lancez la commande `make html`.

Vous pourrez ensuite la consulter en ouvrant le fichier `zds-site/doc/sphinx/build/html/index.html`

### Conseils de developpement

Vous trouverez tout sur [la page dédiée de la documentation](CONTRIBUTING.md)

## En savoir plus

- [Comment déployer ZDS sur un serveur de production ?](doc/deploy.md)
- [Comment contribuer et conseils de développement](CONTRIBUTING.md)
- [Comment contribuer : comprendre comment suivre le workflow (sur zds)](http://zestedesavoir.com/forums/sujet/324/comment-contribuer-comprendre-comment-suivre-le-workflow/)
- [Les détails du workflow utilisé sur Zeste de Savoir](doc/workflow.md)


Zeste de Savoir est basé sur un fork de [Progdupeu.pl](http://progdupeu.pl) ([Dépôt Bitbucket](https://bitbucket.org/MicroJoe/progdupeupl/)).
