=============
Autres outils
=============

Le package ``zds/utils`` contient un certains nombres d'outils transverses.

pdf_generator
-------------

Il s'agit d'une commande qui a pour objectif de donner la possibilité via une ligne de commande de regénerer un ou plusieurs pdf de tutoriels déjà publiés.

La commande à lancer est : ``python manage.py pdf_generator``.

Pour préciser le tutoriel à regenerer, il suffit de rajouter l'argument ``id=125,142,56`` pour regenerer les pdfs des tutos dont l'id est ``125``, ``142``, et ``56``.

.. toctree::
   :maxdepth: 2

   translate
   templatetags
