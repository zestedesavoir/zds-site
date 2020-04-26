===============================================
Raffraichir le nombre de caractère d'un contenu
===============================================

Pour estimer le temps de lecture d'un contenu, nous utilisons le nombre de caractère de celui-ci (sans les fiotures du markdown).

Pour des raisons de performance ce nombre de caractère est calculé au moment de la publication d'un contenu et stocké dans une table.

Pour différente raison (changement de la formule de calcul, recalcul d'un ancien contenu, etc.) on peut avoir envie
de recalculer le nombre de caractères d'un contenu. Cette commande sert exactement à répondre à ce besoin.

.. sourcecode:: bash

    python manage.py adjust_char_count

Le nombre de caractère de tous les contenus publiés sera alors recalculé.

Vous pouvez préciser une liste de contenus, pour celà l'argument ``--id`` existe:

.. sourcecode:: bash

    python manage.py adjust_char_count --id=125,142,56

.. attention::

    Les ``id`` qui ne seraient pas valides sont automatiquement éliminés. Si aucun n'est valide, la commande ne fait rien.
