================================================
Les context_processors (processeurs de contexte)
================================================

Ceux-ci sont localisés dans ``/zds/utils/context_processor.py``.

La doc de Django explique le principe des context_processors comme ceci :

| Un processeur de contexte possède une interface très simple : ce n’est qu’une fonction Python acceptant un paramètre, un objet HttpRequest, et renvoyant un dictionnaire qui est ensuite ajouté au contexte de gabarit. Chaque processeur de contexte doit renvoyer un dictionnaire.
|
| Les processeurs de contexte personnalisés peuvent se trouver n’importe où dans le code. Tout ce que Django demande, c’est que le réglage TEMPLATE_CONTEXT_PROCESSORS contienne le chemin vers le processeur personnalisé.
|


git_version
===========

``git_version`` permet d'ajouter les informations sur la branche et le commit de la version actuelle.

app_settings
============

``app_settings`` permet d'accéder aux variables de ``ZDS_APP`` qui se trouve dans ``settings.py``.