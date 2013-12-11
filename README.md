ZesteDeSavoir
=============
Site internet communautaire codé à l'aide du Framework Django 1.5.

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
* Modifier son profil (bio, site, avatar, singature)
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

Pour plus de détails consultez l'[article dans le wiki](https://github.com/Taluu/ZesteDeSavoir/wiki) (pas encore terminé)
