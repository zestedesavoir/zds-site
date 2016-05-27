==================
Helpers Javascript
==================

Quelques fonctions sont accessibles via jQuery pour manipuler les éléments du site.

$().tooltip()
=============

La fonction ``$(element).tooltip(contenu)`` va ajouter une tooltip au survol de ``element`` avec comme contenu ``contenu``. Si la tooltip existe déjà sur l'élément, la fonction va juste modifier le contenu.

.. figure:: ../images/design/tooltip.png
    :align: center

    Exemple de tooltip utilisé pour les votes

La tooltip sera par défaut au dessus de l'élément, mais ira automatiquement en dessous si le scroll de la fenêtre ne permet pas de l'afficher totalement au dessus.

Cette fonction retourne un objet ``Tooltip`` qui est définie dans le fichier ``assets/js/tooltips.js``, et qui est complètement documenté dans ce fichier.


$(message).karma()
==================

Cette fonction retourne un objet ``Karma`` qui permet de manipuler et mettre à jour les votes d'un message.

``$("#p42").karma().vote("like")`` permet par exemple d'ajouter (ou de l'enlever si l'utilisateur a déjà voté) un +1 sur le post n°42 sur la page.

L'API complète de l'objet ``Karma`` est documentée dans le fichier ``assets/js/karma.js``.
