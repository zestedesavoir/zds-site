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
- Python 2.7
- Pip

### Commandes
Faites les commandes suivantes au fur et à mesure (si l'une d'entre elle échoue, resolvez là avant de continuer)

```console
pip install --user -r requirements.txt
cd scripts && ./UseUpdatedGitPython.sh && cd ..
cd scripts && ./UseUpdatedPythonMarkdownVersion.sh && cd ..
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

Avant de faire une PR, vérifiez que votre code passe tous les tests unitaires en exécutant les commandes suivantes :

```console
python manage.py test forum
python manage.py test member
```

En savoir plus
--------------
- [Comment déployer ZDS sur un serveur de production ?](https://github.com/Taluu/ZesteDeSavoir/blob/dev/doc/deploy.md)
