[![Build Status](https://travis-ci.org/zestedesavoir/zds-site.svg?branch=dev)](https://travis-ci.org/zestedesavoir/zds-site)
[![Coverage Status](https://coveralls.io/repos/github/zestedesavoir/zds-site/badge.svg?branch=dev)](https://coveralls.io/github/zestedesavoir/zds-site?branch=dev)
[![Requirements Status](https://requires.io/github/zestedesavoir/zds-site/requirements.svg?branch=dev)](https://requires.io/github/zestedesavoir/zds-site/requirements/?branch=dev)
[![Dependency Status](https://david-dm.org/zestedesavoir/zds-site.svg)](https://david-dm.org/zestedesavoir/zds-site)
[![Licence GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)

# [Zeste de Savoir](https://zestedesavoir.com)

Site internet communautaire propulsé par le framework [Django](https://www.djangoproject.com/) 1.11 et [Python](https://www.python.org/) 3.
Zeste de Savoir est basé sur un fork de [Progdupeupl](https://pdp.microjoe.org) ([voir le dépôt Git](https://github.com/progdupeupl/pdp_website)).

Jetez donc un coup d’œil à notre [feuille de route](https://github.com/zestedesavoir/zds-site/wiki/Feuille-de-route).

## Contribuer à Zeste de Savoir
### Conseils de développement

Pour bien démarrer, rendez vous sur [la page dédiée](http://docs.zestedesavoir.com/contributing.html). Les détails du *workflow* [sont détaillés ici](http://docs.zestedesavoir.com/workflow.html) (ou [sur ce sujet](http://zestedesavoir.com/forums/sujet/324/comment-contribuer-comprendre-comment-suivre-le-workflow/)).

En contribuant, vous vous engagez à respecter le [Code de Conduite Contributeurs](CODE_OF_CONDUCT.md).

### Installation

La procédure d'installation [est détaillée ici](http://docs.zestedesavoir.com/install.html).

### Données de test

Pour bénéficier de données de test, exécutez la commande suivante:

```console
make generate-fixtures
```

Si vous êtes sur Windows, préférez ceci :

```console
python .\manage.py loaddata (dir .\fixtures\*.yaml)
python .\manage.py load_factory_data .\fixtures\advanced\aide_tuto_media.yaml
```

Cela va créer plusieurs entitées [détaillées ici](https://docs.zestedesavoir.com/utils/fixture_loaders.html#les-donnees-serialisables-pour-une-base-fonctionnelle).
Différents utilisateurs vont être créés, parmis lesquels:

* user/user : Utilisateur normal ;
* ïtrema/ïtrema : Utilisateur de test supplémentaire sans droits ;
* admin/admin : Utilisateur avec les droits d’un staff et d’un admin ;
* dev/dev : Utilisateur dans le groupe des développeurs ;
* decal/decal : le compte qui possède un identifiant ``Profile`` différent de l’identifiant ``user`` pour permettre de tester des cas ou ces id sont différents (voir [#2711](https://github.com/zestedesavoir/zds-site/issues/2711)).

### La documentation complète

[Voir la documentation en ligne](http://docs.zestedesavoir.com/).

Pour générer la documentation en local, rendez-vous dans le répertoire `zds-site/doc/` depuis votre terminal, et lancez la commande `make html` (`make.bat html` sous Windows) qui utilise [Sphinx](http://www.sphinx-doc.org/en/stable/). 
Vous pourrez ensuite la consulter en ouvrant le fichier `zds-site/doc/build/html/index.html` avec votre navigateur.
