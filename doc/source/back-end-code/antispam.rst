.. _module-antispam:

=======================
Module Anti-Spam de ZDS
=======================

Le module ``zds.antispam`` fournit un système de détection de contenu indésirable.

Structure du module
===================
::

    zds/antispam/
    ├── __init__.py
    ├── apps.py
    ├── management/
    ├── receivers.py         # Signaux
    ├── spam_detector.py     # Détection principale
    ├── spam_fields.py       # Champs surveillés
    ├── spam_model_manager.py # Gestion des modèles d'entrainement
    └── tests/               # Tests unitaires

Fonctionnalités principales
===========================
- Détection de spam dans différents types de contenu
- Entraînement de modèles spécifiques par type de contenu
- Système d'alertes automatisées

Composants clés
===============

SpamDetector (spam_detector.py)
-------------------------------
.. autoclass:: zds.antispam.spam_detector.SpamDetector
   :members:
   :undoc-members:

   Principales méthodes:
   - ``check_text(text, content_type)`` → bool
   - ``send_alert(profile, field_name)`` → None

SpamModelManager (spam_model_manager.py)
----------------------------------------
.. autoclass:: zds.antispam.spam_model_manager.SpamModelManager
   :members:
   :undoc-members:

   Fonctionnalités:
   - Entraînement des modèles (``train(content_type)``)
   - Sauvegarde/chargement des modèles

Utilisation typique
===================

Détection simple de la bibliographie:

.. code-block:: python

   from zds.antispam.spam_detector import SpamDetector

   detector = SpamDetector()
   if detector.check_text(user_input, "PROFILE"):
       detector.send_alert(self.clean_profile, "biography")

Entraînement d'un modèle:

.. code-block:: python

   from zds.antispam.spam_model_manager import SpamModelManager

   manager = SpamModelManager()
   manager.train("PROFILE")

Intégration avec les signaux
============================
Le module écoute automatiquement les sauvegardes de modèles via ``receivers.py``.

Tests
=====
Pour lancer les tests:

.. code-block:: bash

   python manage.py test zds.antispam.tests
