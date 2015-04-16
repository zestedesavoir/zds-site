=========================
Structure globale du site
=========================

Le site est composé de plusieurs grandes parties.

L'en-tête
=========

.. figure:: ../images/design/en-tete.png
   :align: center

On peut découper l'en-tête du site en quatre.

Le logo
-------

Le logo est simplement un lien qui a pour contenu une image. L'image change en fonction de la taille de l'écran.

Le menu
-------

Le menu est composé soit d'un lien, soit d'un menu déroulant. Ces derniers contiennent des listes de liens.

.. figure:: ../images/design/en-tete_menu.png
   :align: center

La *logbox*
-----------

La *logbox* contient trois menus déroulants :

- le premier affiche les messages privés ;
- le deuxième affiche les notifications ;
- et le dernier contient des liens vers les zones réservées à l'utilisateur.

Pour le Staff (les membres avec les droits de modération), il existe un autre menu pour les alertes de modération.

.. figure:: ../images/design/en-tete_logbox.png
   :align: center

Le fil d'ariane
---------------

Le fil d'ariane est en deux partie :

- à gauche, une aide à la navigation ;
- à droite, un petit formulaire de recherche.

La barre latérale
=================

La barre latérale contient des listes de liens, boutons ou formulaires permettant à l'utilisateur d'effectuer des actions.

.. figure:: ../images/design/barre-laterale.png
   :align: center

   Barre latérale de la page d'un profil

Le contenu principal
====================

Le contenu principal change radicalement suivant les pages, comme son nom l'indique, il contient le contenu principal, important.

Le bas de page
==============

Le bas de page est sûrement la partie la plus simple du site. Il contient trois *flexboxs* [#flexbox]_ :

- celui de gauche affiche le nom du site ;
- celui du milieu contient les liens vers les comptes des réseaux sociaux du site ;
- celui de droite contient des liens vers les pages annexes du site, tel que les CGUs par exemple.

.. figure:: ../images/design/bas-de-page.png
   :align: center

.. [#flexbox] modèle de boîte flexible en HTML/CSS (`voir le tutoriel sur Alsacréations <http://www.alsacreations.com/tuto/lire/1493-css3-flexbox-layout-module.html>`_)

Le menu pour mobile
===================

Le menu pour mobile est généré à partir de l'en-tête et de la barre latérale grâce à `ce code Javascript <https://github.com/zestedesavoir/zds-site/blob/dev/assets/js/mobile-menu.js>`_.

.. figure:: ../images/design/menu-mobile.png
   :align: center
