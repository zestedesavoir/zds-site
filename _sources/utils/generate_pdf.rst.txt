========================================
Générer les PDFs des différents contenus
========================================

Vous avez la possibilité de générer le (ou les) PDF(s) d'un (ou plusieurs) contenu(s) déjà publié(s) en une commande :

.. sourcecode:: bash

    make generate-pdf # ou la commande suivante :
    python manage.py generate_pdf

Les PDFs de tout les contenus publiés seront alors (re)générés.

.. attention::

    Cette commande supprime le PDF déjà généré.

Vous pouvez préciser une liste de contenus dont les PDF doivent être (re)généré en employant l'argument ``id`` (ou ``ids``). Par exemple, pour générer les PDFs des contenus dont l'id est ``125``, ``142`` et ``56`` if faut mettre:

.. sourcecode:: bash

    python manage.py generate_pdf id=125,142,56

Seuls ces PDFs seront alors (re)générés.

.. attention::

    Les ``id`` qui ne seraient pas valides sont automatiquement éliminés. Si aucun n'est valide, la commande ne fait rien.
