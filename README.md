ZesteDeSavoir
=============
Site internet communautaire codé à l'aide du Framework Django 1.5.

* Lien du site : [zestedesavoir](http://www.zestedesavoir.com)
* Lien de teasing : [Teasing](http://zestedesavoir.com/teasing/)

Fonctionnalités implementées
----------------------------
### La gestion forums
#### Un membre peut :
* Créer un topic
* Editer son topic
* Marquer son topic comme résolu
* Poster dans un topic (avec des smileys)
* Liker/Disliker un post
* Signaler un post aux modérateurs

#### Un staff peut :
* Faire tout ce que fait un membre simple
* Masquer un message alerté
* Marquer n'importe quel sujet comme résolu
* Marquer un sujet en post-it
* Déplacer un topic dans un autre forum
* Verouiller un topic

### La gestion des membres
#### Un membre peut :
* Modifier son profil (bio, site, avatar, signature)
* Modifier ses préférences
    * Affichage publique de son adresse mail
    * Affichage de la signature des membres
    * Menu déroulant au clic ou au survol
* Modifier son mot de passe
* Modifier son pseudo
* Modifier son adresse mail

#### Un staff peut :
* Faire tout ce que fait un membre simple
* bannir un membre (temporaire ou à vie)
* mettre un membre en lecture seule (temporaire ou à vie)

### La gestion des tutoriels
#### Un membre peut :
* Créer un tutoriels (big, mini)
* Importer un tutoriel du sdz au format .tuto
* Consulter l'historique de rédaction
* Envoyer une version de l'historique en validation
* Supprimer son tutoriel/partie/chapitre

#### Un staff peut :
* Faire tout ce que fait un membre simple
* Consulter un tutoriel hors ligne
* Réserver un tutoriel envoyé en validation
* Accepter/Rejeter un tutoriel arrivé en validation

### La gestion des Message Privés
#### Un membre peut :
* Créer un MP
* Ajouter des membres au MP
* Sortir d'un MP sans supprimer la conversation
* Editer son message si la dernière réponse postée est la sienne

#### Un staff peut :
* Faire tout ce que fait un membre simple

Fonctionnalités à venir
-----------------------
Elles sont reportées essentiellement dans le [bugtraker](https://github.com/Taluu/ZesteDeSavoir/issues?state=open)

Comment démarrer une instance de ZdS ?
--------------------------------------
### Pré-requis
- Python 2.7
- Pip
- Ruby
- Ruby Gems

### Commandes
Faites les commandes suivantes au fur et à mesure (si l'une d'entre elle échoue, resolvez là avant de continuer)

```console
gem install compass
gem install zurb-foundation
pip install --user -r requirements.txt
python manage.py syncdb
python manage.py migrate
python manage.py runserver
```
Pour appliquer le pacth de correction du module gitpython, executez :

```console
cd scripts && ./UseUpdatedGitPython.sh && cd ..
```

Pour bénéficier de données statiques, exécutez les commandes suivantes, dans l'ordre, à la fin des précédentes :

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

Si vous voulez utiliser la meme version de python-markdown que sur le serveur, incluant la mise en évidence de lignes de codes particulières exécutez :

```console
cd scripts && ./UseUpdatedPythonMarkdownVersion.sh && cd ..
```

Pour plus de détails consultez l'[article dans le wiki](https://github.com/Taluu/ZesteDeSavoir/wiki) (pas encore terminé)
