===================
Les messages privés
===================

Envoi et participation
======================

Zeste de Savoir fournit un module de messagerie privée qui vous permet de communiquer avec les membres possédant un compte sur le site.

Vous pouvez accéder au module de messagerie privée à tout moment en cliquant sur l'icône :

   .. figure:: ../images//private_message/icone-mp.png
      :align:   center

      Icône d'accès au module de messagerie privée

Lors de l'envoi d'un message privé, vous avez accès à cette interface :

   .. figure:: ../images//private_message/interface-mp.png
      :align:   center

      Interface de rédaction d'un message privé

Tout d'abord, entrez le nom des destinataires de votre message en les séparant par une virgule. L'autocomplétion vous aide à trouver les membres que vous cherchez.

Par conception, la sélection des destinataires a ces propriétés :

- les pseudos sont insensibles à la casse ;
- contacter un membre du groupe ``bot_group`` ou un membre banni vous renverra un message d'erreur expliquant que ledit utilisateur est injoignable ;
- contacter un membre qui n'existe pas vous renverra un message d'erreur expliquant que ledit utilisateur n'existe pas.

Une fois le message envoyé, tous les destinataires reçoivent un mail. Selon les paramètres de leur compte, les participants peuvent également recevoir un mail en cas de réponse à la conversation privée.

Tout participant à la conversation privée sera averti de l'arrivée d'une réponse par une notification sur l'icône du module :

   .. figure:: ../images//private_message/icone-mp-new.png
      :align:   center

      Un nouveau message privé est arrivé

Les règles citées précédemment sont aussi valables lorsque :

- vous ajoutez un participant à la discussion privée a posteriori ;
- vous ajoutez un auteur à un tutoriel ;
- vous ajoutez un auteur à un article.
