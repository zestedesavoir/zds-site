===========
Les Membres
===========

Inscription
===========

L'inscription d'un membre se déroule en deux phases :

- le membre crée son compte et fournit un pseudo, un mot de passe et une adresse mail.
- un mail de confirmation est envoyé avec un jeton qui permettra d'activer le compte.

.. attention::

    Les virgules ne sont pas autorisées dans le pseudonyme, qui ne peut également pas commencer ou finir par des espaces.
    Le mot de passe doit faire au moins 6 caractères.


Désinscription
==============

L'inscription se fait via l'interface utilisateur.

-  Le lien de désinscription est accessible via paramètres (``/membres/parametres/profil/``) puis “Se désinscrire” dans la barre
   latérale (``/membres/desinscrire/attention``) :
   -> |Lien de désinscription| <-
-  Le lien mène alors vers une page expliquant les conséquences de sa
   désinscription avec un bouton rouge en bas de celle-ci :
   -> |Bouton de confirmation| -<
-  Le clic sur le bouton rouge ouvre une boite modale qui constitue le dernier avertissement avant le déclenchement du processus de
   désinscription :
   -> |Boîte modale| <-

.. |Lien de désinscription| image::http:// zestedesavoir.com/media/galleries/978/a5672283-0622-475e-8ea8-67db777d45a6.png.960x960_q85.png
.. |Bouton de confirmation| image:: http://zestedesavoir.com//media/galleries/978/1c036ffd-8e5a-4cfe-aa59-056769420259.png.960x960_q85.png
.. |Boîte modale| image:: http://zestedesavoir.com//media/galleries/978/5ca70620-3e1c-4245-a06c-a9b6771edfa3.png.960x960_q85.png

Le clic sur "me désinscrire" entraîne alors une série d'action qui sont **irréversibles** :

-  Suppression du profil, libèrant le pseudo et l’adresse courriel pour
   les futures inscriptions ;
-  Le membre est déconnecté ;
-  Les données du membre sont anonymisées :

   -  messages du forum ayant comme pseudo ``anonymous`` ;
   -  les sujets du forum restent ouverts mais ont comme auteur ``anonymous`` ;
   -  les messages des MP sont anonymisés (ont comme auteur ``anonymous``) et le membre quitte les discussions auxquelles il participait ;
   -  les commentaires de tutoriels/articles ont comme pseudo ``anonymous`` ;
   -  les `galeries`_ non liées à un tutoriel sont données à ``Auteur externe`` (puisque l’image peut être considérée comme venant d’un “auteur”) avec droit de lecture et d’écriture ;
   -  les `articles`_ et `tutoriels`_ suivent ces règles :

      -  si le tutoriel/article a été écrit par plusieurs personnes : le membre est retiré de la liste des auteurs ;
      -  si le tutoriel/article est *publié*, il passe sur le compte “Auteur externe”, **une demande expresse sera nécessaire au retrait complet de ses contenus** ;
      -  si le tutoriel/article n’est pas publié (brouillon, bêta, validation) il est supprimé ainsi que la galerie associée.

.. _galeries: /gallery/gallery.html
.. _articles: ](.../article/article.html)
.. _tutoriels: .../tutorial/tutorial.html

Les membres dans les environnement de test et de développement
==============================================================

Afin de faciliter les procédures de tests en local, plusieurs utilisateurs ont été créés avec leurs profils via les *fixtures* :

- user/user : Utilisateur normal
- staff/staff : Utilisateur avec les droits d'un staff
- admin/admin : Utilisateur avec les droits d'un staff et d'un admin
- anonymous/anonymous : Utilisateur qui permet l'anonymisation des messages sur les forums, dans les commentaires d'articles et de tutoriels ainsi que dans les MPs
- Auteur externe/external : Utilisateur qui permet de récupérer les tutoriels d'anciens membres et/ou de publier des tutoriels externes.

Pour que ces membres soient ajoutés à la base de données, il vous faudra exécuter la commande, à la racine du site

.. sourcecode:: bash

    python manage.py loaddata fixtures/users.yaml

.. attention::

    Les utilisateurs ``anonymous`` et ``Auteur externe`` **doivent** être présents dans la base de données.


Le cas des utilisateurs ``anonymous`` et ``Auteur externe` est particulier car ils permettent le processus d'anonymisation en cas de désinscription ou de demande expresse du membre.

Ces derniers sont totalement paramétrables dans le fichiers `zds/settings.py` : pour changer le *username* (nom d'utilisateur) de celui qui doit être considéré comme ``anonymous`` ou ``Auteur externe`, agissez sur ces constantes :

.. soucecode:: python

    # Constant for anonymisation

    ANONYMOUS_USER = "anonymous"
    EXTERNAL_USER = "Auteur externe"


