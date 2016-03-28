===============================
Générer les rapports de release
===============================

Vous pouvez générer des rapports de releases via la commande interactive (depuis le dossier racine) :

.. sourcecode:: bash

    make report-release-back # ou la commande suivante :
    python scripts/release_generator.py

Un fichier markdown ``release_summary.md`` sera alors créé avec :

  - Le nom et lien vers la release sur Github
  - Le nombre de tickets inclus dans la release
  - Les tickets triés selon Bug, Évolution ou Non défini
