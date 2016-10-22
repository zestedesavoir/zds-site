============================
Les utilitaires (``utils/``)
============================

Module situé dans ``zds/utils/``. Il regroupe certaines fonctions et objets utiles à tout les autres modules.

.. contents:: Fichiers documentés :

Modèles (``models.py``)
=======================

.. automodule:: zds.utils.models
    :members:

Forums (``forums.py``)
======================

.. automodule:: zds.utils.forums
    :members:

Messages privés (``mps.py``)
============================

.. automodule:: zds.utils.mps
    :members:

Tutoriels (``tutorials.py``)
============================

.. automodule:: zds.utils.tutorials
    :members:

Les processeurs de contexte (``context_processor.py``)
======================================================

La doc de Django explique le principe des *context_processors* comme suit :

| Un processeur de contexte possède une interface très simple : ce n’est qu’une fonction Python acceptant un paramètre, un objet HttpRequest, et renvoyant un dictionnaire qui est ensuite ajouté au contexte de gabarit. Chaque processeur de contexte doit renvoyer un dictionnaire.
|
| Les processeurs de contexte personnalisés peuvent se trouver n’importe où dans le code. Tout ce que Django demande, c’est que le réglage ``TEMPLATE_CONTEXT_PROCESSORS`` contienne le chemin vers le processeur personnalisé.
|

(pour plus de détails, `voir la documenation de Django à ce sujet <https://docs.djangoproject.com/fr/1.8/ref/templates/api/#subclassing-context-requestcontext>`__)

.. automodule:: zds.utils.context_processor
    :members:

Utilitaires pour formulaires (``forms.py``)
===========================================

.. automodule:: zds.utils.forms
    :members:


Autres (``misc.py``)
====================

.. automodule:: zds.utils.misc
    :members:

