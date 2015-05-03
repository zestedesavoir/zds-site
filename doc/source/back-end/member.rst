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

   .. figure:: ../images/member/desinscription-1.png
      :align:   center

      Position du lien de désinscription dans les paramètres du membre (``/membres/parametres/profil/``)

-  Le lien mène alors vers une page expliquant les conséquences de sa  désinscription. Il peut alors poursuivre via un bouton en bas de celle-ci :

   .. figure:: ../images/member/desinscription-2.png
      :align:   center

      Bouton de confirmation


-  Le clic sur le bouton rouge ouvre une boite modale qui constitue le dernier avertissement avant le déclenchement du processus de désinscription :

   .. figure:: ../images/member/desinscription-3.png
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

L'interface de karma
--------------------

Pour pouvoir communiquer entre modérateur, il est utile d'avoir un outil de suivi sur les membres. Ce dernier prend forme via la gestion du "karma" d'un membre. Le karma est une valeur numérique pouvant aller de -100 à +100. Cette valeur peut-être modifié via l'ajout de bonus/malus par les modérateurs. Chaque modification du karma doit s'accompagner d'un commentaire, mais un commentaire n'entraine pas forcément une modification du karma (0 point de bonus/malus).

Cet outil à deux rôles. Permettre d'identifier les membres *perturbateurs* mais aussi les membres *moteurs* qui pourrait faire l'objet d'un article ou d'une mise en avant de leurs projets.

Pour modifier le karma d'un membre, il faut donc être modérateur sur le site. Sur la fiche profil d'un membre apparait alors un formulaire pour ajouter un bonus/malus et une liste des modifications précédentes montrant l'impact (+/-), le message, l'auteur du bonus/malus et la date d'effet de ce dernier.

L'interface de réinitialisation de mot de passe
-----------------------------------------------

Quand le membre du site oublie son mot de passe, il peut le réinitialiser. L'ancien mot de passe est supprimé et l'utilisateur peut en choisir un nouveau.
Pour cela, il se rend sur la page de réinitialisation de mot de passe (``membres/reinitialisation/``) à partir de la page de connexion.

    .. figure:: ../images/member/reinitialisation-mot-de-passe-1.png

Sur cette page l'utilisateur, doit rentrer son nom d'utilisateur ou son adresse de courriel. Pour cela, il clique sur le lien pour que le formullaire apparaisse.
Quand l'utilisateur clique sur le bouton de validation, un jeton est généré aléatoirement et est stocké dans une base de données.

Un message est envoyé à l'adresse de courriel de l'utilisateur. Ce courriel contient un lien de réinitialisation. Ce lien contient un paramètre, le jeton de réinitialisation et dirige l'utilisateur vers l'adresse ``membres/new_password/``.

    .. figure:: ../images/member/reinitialisation-mot-de-passe-2.png

Cette page permet de changer le mot de passe de l'utilisateur. L'utilisateur remplit le formulaire et clique sur le bouton de validation.
Si le mot de passe et le champ confirmation correspondent et que le mot de passe respecte les règles métiers, le mot de passe est changé.
Le systéme affiche un message de confirmation du changement du mot de passe.

.. attention::

    - Il n'existe aucune restriction sur le nombre de demande de réinitialisation
    - Un utilisateur peut avoir le même nom d'utilisateur que l'adresse email de quelqu'un d'autre. Exemple:

         ================  =======================
          username        	email
         ================  =======================
          firm1 	       firm1@gmail.com
          firm1@gmail.com  firm1@zestedesavoir.com
         ================  =======================
.. attention::

    - Le mot de passe doit faire au moins 6 caractères.
    - Le lien est valable une heure. Si l'utilisateur ne clique pas sur le lien dans le temps imparti, un message d'erreur est affiché.
    - Le jeton de réinitialisation de mot de passe n'est valide qu'une seule fois. Si l'utilisateur tente de changer son mot de passe avec le même jeton, une page 404 est affiché à l'utilisateur.