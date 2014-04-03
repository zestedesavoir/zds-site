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
- Python 2.7 (avec les fichiers de developpement, la paquet `python-dev` sous Ubuntu)
- Pip
- git

**NB : les commandes suivantes sont génériques et indépendantes de la distribution que vous utilisez. Si votre distribution propose Python2 par defaut (comme Ubuntu), les commandes `/usr/bin/env python2` peuvent être remplacées par `python` tout simplement.**

### Commandes
Faites les commandes suivantes au fur et à mesure (si l'une d'entre elle échoue, resolvez là avant de continuer)

```console
pip install --user -r requirements.txt
cd scripts && sudo ./UseUpdatedGitPython.sh && cd ..
cd scripts && sudo ./UseUpdatedPythonMarkdownVersion.sh && cd ..
/usr/bin/env python2 manage.py syncdb
/usr/bin/env python2 manage.py migrate
/usr/bin/env python2 manage.py runserver
```
**NB : si une commande ne marche pas, vérifier pourquoi avant de continuer**

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
python manage.py test member forum tutorial mp
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](https://github.com/Taluu/ZesteDeSavoir/blob/dev/doc/deploy.md)
