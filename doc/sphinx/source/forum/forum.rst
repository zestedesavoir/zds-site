==========
Les forums
==========

Il y a sur Zeste de Savoir, un espace communautaire permettant aux membres, d'échanger entre eux sur divers sujets. Cette espace est comunément appelé « forums ».
L'URL permettant d'accéder à ce service est : ``/forums``, simplement. 

Le découpage des forums
=======================

La modération des forums
========================

Sur Zeste de Savoir, une modération des forums, autant sur les sujets, que sur les messages inclus, est faite par les membres possèdant un certain rang. Cette dernière, permet d'éviter tout débordement ou autre. 

La modération des sujets
------------------------

<<<<<<< HEAD
=======
Tout d'abord, il y a une posibilité de faire de la modération par sujet. Ici, cette modération s'effectue grâce aux liens se trouvant dans *sidebar* (zone se trouvant sur le côté gauche de la page).
  ..figure:: images/modo_forum_sujet.png
    :align: center

Nous retrouvons ici, trois items :

-   **Fermer le sujet** : ici, le but est de fermer le sujet. Ce qui empêchera quiconque de poster dedans. Un cadena, apparaîtra aussi à côté du sujet sur la liste des sujets de la catégorie, et, l'encart suivant fera alors son apparition sur le sujet en lui-même :
    
    .. figure:: images/sujet_ferme.png
        :align:   center

-   **Marquer en post-it** : le sujet sera mis en post-it sur la catégorie dans laquelle il se trouve. Ce qui fait qu'il surpassera tout les autres sujets et cela, même si une réponse plus récente vient d'être posté dans un autre sujet. Il ne **pourra jamais se retrouver en-dessous des autres**. Lors de la mise en post-it, une épingle apparaît à côté du sujet dans la catégorie où il se trouve.
  
    .. figure:: images/post_it.png
        :align:   center

-   **Déplacer le sujet** : cet item permet de faire un déplacement de sujet, au cas-où un membre se serait trompé en postant. Cela évite qu'il ait à recréer un sujet et donc un doublon de celui-ci. Le déplacement, se fait via une modale :
    
    .. figure:: images/deplacement.png
        :align:   center

>>>>>>> Étoffement de la doc sur les forums
La modération des messages
--------------------------

Il est aussi possible d'effectuer la modération plus finement, en ciblant des messages en particulier dans des sujets. Cela se fait grâce aux différents liens qui se trouvent sur les messages :
  
  .. figure:: images/modo_message.png
      :align:   center



Les filtres sur les sujets
==========================

Dans un forum
-------------

Il existe actuellement 3 filtres pour filtrer les sujets dans un forum :

* Sujets résolus (`solve`)
* Sujets non résolus (`unsolve`)
* Sujets sans réponse (`noanswer`)

Il suffit d'ajouter `?filter=<filtre>` à l'URL en remplaçant `<filtre>` par un des 3 filtre ci-dessus.
