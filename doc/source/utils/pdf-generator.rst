==============================
Générer les PDFs des tutoriels
==============================

Vous avez la possibilité de générer le (ou les) PDF(s) d'un (ou plusieurs) tutoriel(s) déjà publié(s) en une commande :

.. sourcecode:: bash

    python manage.py pdf_generator

Pour préciser le (ou les) tutoriel(s) à générer, il suffit de rajouter l'argument ``id``. Par exemple, pour générer les pdfs des tutoriels dont l'id est ``125``, ``142``, et ``56`` if faut mettre ``id=125,142,56``.