============
Installation
============

Pour utiliser (et éventuelement modifier) Zeste de Savoir, il est nécessaire de télécharger le dépot. Un `compte Github <https://github.com/join>`_ est nécessaire si vous souhaitez contribuer.

La première étape est de créer `un fork <https://help.github.com/articles/fork-a-repo/>`_: une fois connecté à votre compte Github, rendez-vous `sur la page du dépot zds-site <https://github.com/zestedesavoir/zds-site>`_ et cliquez sur "Fork" en haut à droite.

Pour la suite, vous avez besoin de l'outil ``git``, qui peut être trouvé dans le gestionnaire de paquet de votre distribution (Linux et macOS) ou `téléchargé <https://git-scm.com/downloads>`_.

Ensuite, utilisez les commandes suivantes:

.. sourcecode:: bash

   git clone https://github.com/<VOTRE_LOGIN>/zds-site.git
   cd zds-site
   git remote add upstream https://github.com/zestedesavoir/zds-site.git
   git fetch upstream

où ``<VOTRE_LOGIN>`` doit être remplacé par votre login sur Github, afin de télécharger votre *fork*.

Si vous souhaitez terminer d'installer puis démarrer une instance locale de ZdS, cliquez sur le lien correspondant à votre système d'exploitation.

.. toctree::
   :maxdepth: 1
   :glob:

   install/install-*

Les détails concernant la contribution au code du site peuvent être trouvés `ici <./contributing.html>`_.

Quelques informations supplémentaires:

.. toctree::
   :maxdepth: 2
   :glob:

   install/extra-*
