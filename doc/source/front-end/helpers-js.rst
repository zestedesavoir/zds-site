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

.. note::

   Si vous n'avez besoin que d'infobulles simples, sans avoir à y mettre du contenu HTML riche ou à réagir au clic ou
   autre sur ces dernières, `préférez utiliser les plus simples et légères infobulles CSS, d'apparence identique <elements-specifiques-au-site.html#les-infobulles-css>`_.


$(message).karma()
==================

Cette fonction retourne un objet ``Karma`` qui permet de manipuler et mettre à jour les votes d'un message.

``$("#p42").karma().vote("like")`` permet par exemple d'ajouter (ou de l'enlever si l'utilisateur a déjà voté) un +1 sur le post n°42 sur la page.

L'API complète de l'objet ``Karma`` est documentée dans le fichier ``assets/js/karma.js``.


``window.ajax``
===============

Afin de faciliter la migration du code JS du site pour ne plus utiliser JQuery,
nous avons créé un helper ajax qui vous permettra de manipuler rapidement les
requêtes vers les fonctionnalités du site qui prennent un formulaire ou du json en entrée
et retournent un json en réponse.

Cet objet est défini dans  ``assets/js/common/ajax.js``. Il vous permet d'appeler nativement
les méthodes get/post/put et sera vu par django comme un appel ajax.
Vous pourrez à chaque fois définir une méthode à appeler en cas de succès de la **communication**
(c'est-à-dire si la requête a pu être envoyée au serveur et obtenir un retour au format json, peu importe son code de retour)
et en cas d'erreur.

La première méthode prend en argument un objet issu de la désérialisation du JSON.

Exemple:

.. sourcecode:: javascript

	const form = document.querySelector('.monFormulaire')
    const data = new FormData(form)
    ajax.post(form.getAttribute('action'), data,
      result) => maFonctionEnCasDeSucces(result.une_valeur_retournee_par_le_serveur),
      () => maFonctionEnCasDEchec()
    )
