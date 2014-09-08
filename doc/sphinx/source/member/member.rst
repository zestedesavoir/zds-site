===========
Les Membres
===========

Inscription
===========

L'inscription d'un membre se déroule en deux phases :

- le membre crée son compte et fournit un pseudo, un mot de passe et une adresse mail.
- un mail de confirmation est envoyé avec un jeton qui permettra d'activer le compte.

.. attention::

    les virgules ne sont pas autorisées dans le pseudonyme


Désinscription
==============

Interface utilisateur (front)
_____________________________

- Lien de désinscription accessible via Paramètres (en en haut à droite de toute les pages sur l'avatar / roue dentée) puis Désinscription dans la barre latérale ;
- Le lien mène alors vers une page expliquant les conséquences de sa désinscription avec un bouton rouge en bas de celle-ci ;
- Le clic sur le bouton rouge ouvre une boite modale qui constitue le dernier avertissement avant le déclenchement du processus de désinscription.

Effets de la désinscription (back)
__________________________________

- Suppression du profil, libèrant le pseudo et l'adresse courriel pour les futures inscriptions ;
- Le membre est déconnecté ;
- Les données du membre sont anonymisées :
     - messages du forum ayant comme pseudo "Anonyme" ;
          - les sujets du forum restent ouverts mais ont comme auteur "Anonyme" ;
          - les galeries non liées à un tutoriel sont données à "Auteur externe" (puisque l'image peut être considérée comme venant d'un "auteur") avec droit de lecture et d'écriture ;
          - les MP sont anonymisés et le membre quitte les discussions auxquelles il participait ;
     - les commentaires de tutoriels/articles ont comme pseudo "Anonyme" ;
     - les articles et tutoriels suivent ces règles :
          - si le tutoriel/article a été écrit par plusieurs personne; le membre est retiré de la liste des auteurs ;
          - si le tutoriel/article est publié*, il passe sur le compte "Auteur externe", une demande expresse sera nécessaire au retrait complet de ses contenus ;
          - si le tutoriel/article n'est pas publié (brouillon, bêta, validation) il est supprimé ainsi que la galerie associée.


Les membres dans les environnement de test et de développement
==============================================================

Afin de faciliter les procédures de tests en local, plusieurs utilisateurs ont été créés avec leurs profiles.

- user/user : Utilisateur normal
- staff/staff : Utilisateur avec les droits d'un staff
- admin/admin : Utilisateur avec les droits d'un staff et d'un admin
- anonymous/anonymous : Utilisateur qui permet l'anonymisation des messages sur les forums
- Auteur externe/external : Utilisateur qui permet de récupérer les tutoriels d'anciens membres et/ou de publier des tutoriels externes.

Pour que ces membres soient ajoutés à la base de données, il vous faudra exécuter la commande, à la racine du site

.. sourcecode:: bash

    python manage.py loaddata fixtures/users.yaml

.. attention::

    Les utilisateurs `anonymous` et `Auteur externe` **doivent** être présents dans la base de données.


Le cas des utilisateurs `anonymous` et `Auteur externe` est particulier car ils permettent le processus d'anonymisation en cas de désinscription ou de demande expresse du membre.

Ces derniers sont totalement paramétrables dans le fichiers `zds/settings.py`.
Pour changer le *username* (nom d'utilisateur) considéré comme `anonymous` ou `Auteur externe`, agissez sur ces constantes :

.. soucecode:: python

# Constant for anonymisation

ANONYMOUS_USER = "anonymous"
EXTERNAL_USER = "Auteur externe"


