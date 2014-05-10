#Serveur de PreProd

Actuellement le serveur de preprod est visible à l'adresse suivante : preprod.zestedesavoir.com

##Configuration du serveur

- Adresse IP : 178.32.53.245
- Utilisateur actuel : root
- Mot de passe : _Demande Privée_
- OS : Gnu/Linux Debian Wheezy
- Serveur Web : Nginx
- Moteur wsgi : Gunicorn
- SGBD : PostgreSQL
- Programme de gestion des taches : supervisor

##Déploiement à partir de zero

### installation des outils

- python, 
- virtualenv (dans /opt/zdsenv/), 
- git

###Clone du repo

- `git clone https://github.com/Taluu/ZesteDeSavoir.git`
- `mkdir tutoriels-private`
- `mkdir tutoriels-public`
- `mkdir articles-data`
- `touch zds/settings_prod.py`
- `vim zds/settings_prod.py`

On édite le fichier de manière à rajouter les infos spécifiques à la preprod. Pour l'exemple, le contenu actuel du fichier de settings_prod.py sur la preprod est le suivant :
```text
#DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'zdsdb',
        'USER': 'zds',
        'PASSWORD': 'mot_de_passe',
        'HOST': 'localhost',
        'PORT': '',
    }
}

EMAIL_HOST = 'mail.geoffreycreation.com'
EMAIL_HOST_USER = 'zds@geoffreycreation.com'
EMAIL_HOST_PASSWORD = 'mot_de_passe'
EMAIL_PORT = 25
```


##Déploiement à partir d'un existant

###Mise à jour du repo

`git pull`

###Arret du process gunicorn en cours

`ps -x`

le retour nous renvoit l'ensemble des processus qui tournent actuellement. Il y'en a normalement 5 labelisés avec python. Il faudra demander au premier processus parmi ces cinq de s'éteindre. Pour cela, il faut noter le PID et faire la commande suivante :

`kill -15 <num_pid>`

Si par hasard ceci ne fonctionne pas, il faut prendre les grands moyens et le buter :

`kill -9 <num_pid>`

###Migration de la bd
`python manage.py migrate`

###Connexion à l'environnement zds

- `cd /opt/zdsenv/ZesteDeSavoir`
- `source ../bin/activate `
- `gunicorn_django --workers=4 --bind 178.32.53.245:8001`

Pour passer le process en arrire plan, faites Ctrl+Z et taper la commande suivante :

- `bg`
