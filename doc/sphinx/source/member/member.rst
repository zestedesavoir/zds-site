===========
Les membres
===========

Inscription
===========

L'inscription d'un membre se déroule en deux phases :

- Le membre crée son compte et fournit un pseudo, un mot de passe et une adresse mail valide.
- Un mail de confirmation est envoyé avec un jeton qui permettra d'activer le compte.

.. attention::

    - Les virgules ne sont pas autorisées dans le pseudonyme, qui ne peut également pas commencer ou finir par des espaces.
    - Le mot de passe doit faire au moins 6 caractères.


Désinscription
==============

L'inscription se fait via l'interface utilisateur.

-  Le lien de désinscription est accessible via paramètres (``/membres/parametres/profil/``) puis “Se désinscrire” dans la barre
   latérale (``/membres/desinscrire/avertissement/``) :

   .. figure:: images/desinscription-1.png
      :align:   center

      Position du lien de désinscription dans les paramètres du membre (``/membres/parametres/profil/``)

-  Le lien mène alors vers une page expliquant les conséquences de sa  désinscription. Il peut alors poursuivre via un bouton en bas de celle-ci :

   .. figure:: images/desinscription-2.png
      :align:   center

      Bouton de confirmation


-  Le clic sur le bouton rouge ouvre une boite modale qui constitue le dernier avertissement avant le déclenchement du processus de désinscription :

   .. figure:: images/desinscription-3.png
      :align:   center

      La dernière étape


Le clic sur "me désinscrire" entraîne alors une série d'action (qui sont **irréversibles**) :

-  Suppression du profil, libèrant le pseudo et l’adresse courriel pour les futures inscriptions ;
-  Le membre est déconnecté ;
-  Les données du membre sont anonymisées :

   -  le pseudo ``anonymous`` est employé :
        -  pour les sujets du forum (qui, cependant, restent ouverts)
        -  pour les messages des MP (le membre quitte les discussions auxquelles il participait) ;
        -  pour les commentaires aux tutoriels et articles ;
   -  les `galeries`_ non liées à un tutoriel sont données à ``external`` (puisque l’image peut être considérée comme venant d’un “auteur”) avec droit de lecture et d’écriture ;
   -  les `articles`_ et `tutoriels`_ suivent ces règles :

      -  si le tutoriel/article a été écrit par plusieurs personnes : le membre est retiré de la liste des auteurs ;
      -  si le tutoriel/article est *publié*, il passe sur le compte “external”. Une demande expresse sera nécessaire au retrait complet de ces contenus ;
      -  si le tutoriel/article n’est pas publié (brouillon, bêta, validation) il est supprimé, ainsi que la galerie qui lui est associée.

.. _galeries: ../gallery/gallery.html
.. _articles: ../article/article.html
.. _tutoriels: ../tutorial/tutorial.html


Les membres dans les environnement de test et de développement
==============================================================

Afin de faciliter les procédures de tests en local, 6 utilisateurs ont été créés via la fixture ``users.yaml`` (utilisateur/mot de passe):

- user/user : Utilisateur normal
- staff/staff : Utilisateur avec les droits d'un staff
- admin/admin : Utilisateur avec les droits d'un staff et d'un admin
- anonymous/anonymous : Utilisateur qui permet l'anonymisation des messages sur les forums, dans les commentaires d'articles et de tutoriels ainsi que dans les MPs
- external/external : Utilisateur qui permet de récupérer les tutoriels d'anciens membres et/ou de publier des tutoriels externes.
- ïtrema/ïtrema : Utilisateur de test supplémentaire sans droit

Pour que ces membres soient ajoutés à la base de données, il est donc nécéssaire d'exécuter la commande, suivante, à la racine du site

.. sourcecode:: bash

    python manage.py loaddata fixtures/users.yaml

.. attention::

    Les utilisateurs ``anonymous`` et ``external`` **doivent** être présents dans la base de données pour le bon fonctionnement du site.
    En effet, ils permettent le bon fonctionnement du processus d'anonymisation (voir `plus haut <#desinscription>`_)

Les utilisateurs ``anonymous`` et ``external`` sont totalement paramétrables dans le fichier ``zds/settings.py`` :
pour changer le nom d'utilisateur (*username*) de ces comptes, agissez sur les constantes suivantes (du dictionnaire ZDS_APP):

.. sourcecode:: python

    # Constant for anonymisation

    anonymous_account = "anonymous"
    external_account = "external"

Bien entendu, les comptes correspondants doivent exister dans la base de donnée.

L'interface de promotion
------------------------

Afin de pouvoir gérer les membres directement depuis le site (c'est à dire sans avoir besoin de passer par l'interface d'administration de Django), une interface de promotion a été développée.
Cette interface permet de :
1. Ajouter/Supprimer un membre dans un/des groupe(s)
2. Ajouter/Supprimer le statut super-utilisateur à un membre
3. (Dés)activer un compte

Le premier point permet notamment de passer un membre dans le groupe staff ou développeur. Si d'autres groupes voient le jour (valido ?) alors il sera possible ici aussi de le changer.
Le second point permet de donner accès au membre à l'interface Django et à cette interface de promotion.
Enfin, le dernier point concerne simplement l'activation du compte (normalement faite par le membre à l'inscription).

Elle est géré par le formulaire `PromoteMemberForm` présent dans le fichier `zds/member/forms.py`.
Elle est ensuite visible via le template `member/settings/promote.html` qui peut-être accédé en tant que super-utilisateur via le profil de n'importe quel membre.
