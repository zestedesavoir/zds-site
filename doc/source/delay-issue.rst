=================================
Problème de lenteur lors du dev ?
=================================

Le changement de page est très lent !
--------------------------------------

Désactiver la barre de debug réduit la vitesse de chargement par 10. Si vous n'utilisez pas la ``DEBUG_TOOLBAR_CONFIG``, vous pouvez la désactiver avec la configuration ``dev_fast`` :

.. sourcecode:: bash

    python manage.py runserver --settings zds.settings.dev_fast

Si vous utilisez ``make`` pour lancer le site, il est encore plus simple d'activer ce mode :

.. sourcecode:: bash

    make run-fast

Attention, cela activera aussi le cache côté client des fichiers statiques, ce qui veut dire que les fichiers JS et CSS ne seront pas actualisés sans un rafraîchissement de force (``Ctrl + F5`` ou similaire).
