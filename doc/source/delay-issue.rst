=========================
Problème de lenteur lors du dev ?
=========================

J'ai des lenteurs avec gulp (build|watch)
---------------------

Pour le développement et uniquement ce but, notre script `gulp` prend en entrée un paramètre "--speed" qui désactive les optimisations du code pour la prod. Ainsi `watch` à besoin de calculer moins de choses donc moins d'usage de CPU.

Avec gulp il faudra faire :

.. sourcecode:: bash
    $ npm run watch -- --speed


Le changement de page est très lent !
---------------------

Désactiver la barre de debug réduit la vitesse de chargement par 10. Si vous n'utilisez pas la DEBUG_TOOLBAR_CONFIG, vous pouvez la désactiver avec la commande ci-dessous au démarrage :

Pour ce faire utilisez la configuration `dev_fast` qui désactive la Toolbar :

.. sourcecode:: bash
    python manage.py runserver --settings zds.settings.dev_fast
