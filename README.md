[![Build Status](https://travis-ci.org/zestedesavoir/zds-site.svg?branch=dev)](https://travis-ci.org/zestedesavoir/zds-site)
[![Coverage Status](https://coveralls.io/repos/zestedesavoir/zds-site/badge.png?branch=dev)](https://coveralls.io/r/zestedesavoir/zds-site?branch=dev)
[![Code Health](https://landscape.io/github/zestedesavoir/zds-site/dev/landscape.svg)](https://landscape.io/github/zestedesavoir/zds-site/dev)

[![Requirements Status](https://requires.io/github/zestedesavoir/zds-site/requirements.svg?branch=dev)](https://requires.io/github/zestedesavoir/zds-site/requirements/?branch=dev)
[![Dependency Status](https://david-dm.org/zestedesavoir/zds-site.svg)](https://david-dm.org/zestedesavoir/zds-site)

[![Licence GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)
[![Documentation Status](https://readthedocs.org/projects/zds-site/badge/?version=latest)](https://readthedocs.org/projects/zds-site/?badge=latest)

# Zeste de Savoir

Site internet communautaire codé à l'aide du framework [Django](https://www.djangoproject.com/) 1.7 et de [Python](https://www.python.org/) 2.7.

[Voir l'instance en ligne](https://zestedesavoir.com).


## Fonctionnalités implémentées

- Tutoriels
- Articles
- Membres
- Forums
- Messages privés
- Galeries d'images
- Recherche


## Fonctionnalités à venir

Elles sont reportées essentiellement dans le [*bug tracker*](https://github.com/zestedesavoir/zds-site/issues).


## Comment démarrer une instance de ZdS ?

### Installation d'une version locale de ZdS

- [Installation du backend sur Windows](http://zds-site.readthedocs.org/fr/latest/install/backend-windows-install.html)
- [Installation du backend sur Linux](http://zds-site.readthedocs.org/fr/latest/install/backend-linux-install.html)
- [Installation du backend sur OS X](http://zds-site.readthedocs.org/fr/latest/install/backend-os-x-install.html)
- [Installation du frontend](http://zds-site.readthedocs.org/fr/latest/install/frontend-install.html)
- [Installation de Solr](http://zds-site.readthedocs.org/fr/latest/install/install-solr.html) pour gérer la recherche


### Mettre à jour votre version locale de ZdS

Après avoir mis à jour votre dépôt, vous devez exécuter les commandes suivantes (depuis la racine de votre projet) pour mettre à jour les dépendances.

```console
pip install --upgrade -r requirements.txt -r requirements-dev.txt
python manage.py migrate
```


### Données de test

Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
python manage.py loaddata fixtures/*.yaml
python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml
```

Cela va créer plusieurs entitées :

* 6 utilisateurs (utilisateur/mot de passe) :
	* user/user : Utilisateur normal
	* staff/staff : Utilisateur avec les droits d'un staff
	* admin/admin : Utilisateur avec les droits d'un staff et d'un admin
	* anonymous/anonymous : Utilisateur qui permet l'anonymisation des messages sur les forums
	* Auteur externe/external : Utilisateur qui permet de récupérer les tutoriels d'anciens membres et/ou de publier des tutoriels externes.
	* ïtrema/ïtrema : Utilisateur de test supplémentaire sans droit
* 3 catégories
* 11 forums
* 3 sujets avec une réponse
* 1 message privé (MP) avec 3 participants
* 3 catégories et 2 sous-catégories
* 4 aides pour l'écriture des tutoriels
* 5 unes misent en avant sur la page d'accueil

Pour en savoir plus sur cette commande, [consulter la documentation](http://zds-site.readthedocs.org/fr/latest/utils/fixture_loaders.html).

### La documentation complète

[Voir la documentation en ligne](http://zds-site.readthedocs.org).

La documentation de ZdS est générée par Sphinx, et elle doit être mise à jour à chaque modification ou ajout d'une fonctionnalité du site. Les sources se trouvent [ici](doc/source/).

Pour générer la documentation en local, rendez-vous dans le répertoire `zds-site/doc/` depuis votre terminal, et lancez la commande `make html`. Vous pourrez ensuite la consulter en ouvrant le fichier `zds-site/doc/build/html/index.html`


### Conseils de développement

Vous trouverez tout sur [la page dédiée de la documentation](CONTRIBUTING.md)


## En savoir plus

- [Comment déployer ZDS sur un serveur de production ?](http://zds-site.readthedocs.org/fr/latest/install/deploy-in-production.html)
- [Comment contribuer et conseils de développement](CONTRIBUTING.md)
- [Comment contribuer : comprendre comment suivre le workflow (sur zds)](http://zestedesavoir.com/forums/sujet/324/comment-contribuer-comprendre-comment-suivre-le-workflow/)
- [Les détails du workflow utilisé sur Zeste de Savoir](http://zds-site.readthedocs.org/fr/latest/workflow.html)

Zeste de Savoir est basé sur un fork de [Progdupeupl](https://pdp.microjoe.org) ([voir le dépôt Git](http://git.microjoe.org/progdupeupl/)).
