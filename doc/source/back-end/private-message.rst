===================
Les messages privés
===================

Envoi et participation
======================

ZDS fournit un module de messagerie privée qui vous permet de communiquer avec les membres possédant un compte sur le site.

Vous pouvez accéder au module de message privé à tout moment en cliquant sur l'icône :

   .. figure:: ../images//private_message/icone-mp.png
      :align:   center

      Icône d'accès au module de message privé

Lors de l'envoi du message privé, vous avez accès à cette interface :

   .. figure:: ../images//private_message/interface-mp.png
      :align:   center

      Interface de rédaction d'un message privé

Tout d'abord, entrez le nom de vos destinataires en les séparant d'une virgule. L'autocomplétion vous aide à trouver les membres que vous cherchez.

Par conception, la sélection des destinataires a ces propriétés :

- insensible à la casse;
- contacter un membre du groupe ``bot_group`` vous renverra un message d'erreur expliquant que ledit utilisateur est injoignable;
- contacter un membre qui n'existe pas vous renverra un message d'erreur expliquant que ledit utilisateur n'existe pas.

Une fois le message envoyé, tous les destinataires reçoivent un mail. Aucun autre mail ne sera envoyé au fur et à mesure de la discussion.

Tout participant à la discussion verra l'icône du module notifier l'arrivée d'un message privé :

   .. figure:: ../images//private_message/icone-mp-new.png
      :align:   center

      Un nouveau message privé est arrivé

Les règles citées précédemment sont aussi valables lorsque :

- vous ajoutez un participant à la discussion privée a posteriori;
- vous ajoutez un auteur à un tutoriel;
- vous ajoutez un auteur à un article.