[![Build Status](https://travis-ci.org/zestedesavoir/zds-site.svg?branch=dev)](https://travis-ci.org/zestedesavoir/zds-site)
[![Coverage Status](https://coveralls.io/repos/zestedesavoir/zds-site/badge.png?branch=dev)](https://coveralls.io/r/zestedesavoir/zds-site?branch=dev)
[![Licnce GPL](http://img.shields.io/badge/license-GPL-yellow.svg)](http://www.gnu.org/licenses/quick-guide-gplv3.fr.html)





Zeste de Savoir
===============

Site internet communautaire codé à l'aide du framework [Django](https://www.djangoproject.com/) 1.6 et de [Python](https://www.djangoproject.com/) 2.7.

* Lien du site : [zestedesavoir](http://www.zestedesavoir.com)





Fonctionnalités implementées
----------------------------

- Membres
- Tutoriels
- Articles
- Forums
- Messages privés
- Galeries d'images
- Recherche





Fonctionnalités à venir
-----------------------

Elles sont reportées essentiellement dans le [bugtraker](https://github.com/zestedesavoir/zds-site/issues).





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
```


### Données de test
Pour bénéficier de données de test, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

```console
python manage.py loaddata fixtures/*.yaml

```

Cela va créer plusieurs entitées :

* 5 utilisateurs (utilisateur/mot de passe) :
	* user/user : Utilisateur normal
	* staff/staff : Utilisateur avec les droits d'un staff
	* admin/admin : Utilisateur avec les droits d'un staff et d'un admin
	* anonymous/anonymous : Utilisateur qui permet l'anonymisation des messages sur les forums
	* Auteur externe/external : Utilisateur qui permet de récupérer les tutoriels d'anciens membres et/ou de publier des tutoriels externes.
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

Avant de faire une Pull Request (PR), vérifiez que votre code passe tous les tests unitaires et qu'il est compatible [PEP-8](http://legacy.python.org/dev/peps/pep-0008/) en exécutant les commandes suivantes, pour le back :

```console
python manage.py test
flake8 --exclude=migrations,urls.py --max-line-length=120 --ignore=F403,E126,E127,E128 zds
```

Pour le front :

```console
gulp test
```

Si vous modifiez le modèle (les fichiers models.py), n'oubliez pas de créer les fichiers de migration :

```console
python manage.py schemamigration app_name --auto
```

Si vous avez une connexion lente et que vous ne voulez travailler que sur une branche précise, vous pouvez toujours ne récupérer que celle-ci :

```console
git clone https://github.com/zestedesavoir/zds-site.git -b LA_BRANCHE --depth 1
```



En savoir plus
--------------

- [Comment déployer ZDS sur un serveur de production ?](doc/deploy.md)
- [Contribuer](CONTRIBUTING.md)
- [Comment contribuer : comprendre comment suivre le workflow (sur zds)](http://zestedesavoir.com/forums/sujet/324/comment-contribuer-comprendre-comment-suivre-le-workflow/)





Zeste de Savoir est basé sur un fork de [Progdupeu.pl](http://progdupeu.pl) ([Dépôt Bitbucket](https://bitbucket.org/MicroJoe/progdupeupl/)).
