========================================
Installation et utilisation de zmarkdown
========================================

`zmarkdown <https://github.com/zestedesavoir/zmarkdown>`_ est l'outil permetant de transformer le `markdown (en) <https://daringfireball.net/projects/markdown/syntax>`_ (avec quelques additions spécifiques à ZdS) en HTML ou LaTeX.
Celui-ci est utilisé via un `serveur HTTP <https://github.com/zestedesavoir/zmarkdown/tree/master/packages/zmarkdown>`_ (via `pm2 <https://pm2.keymetrics.io/>`_), qu'il est nécessaire de démarer (voir plus loin) et que ZdS interroge ensuite pour effectuer le rendu du markdown.

Installation
============

.. note::

    L'utilisation de zmarkdown requiere d'avoir installé node et npm, qui est déjà utilisé `par le front-end <extra-install-frontend.html>`_.
    L'installation de ces outils peut être faite via `nvm <https://github.com/creationix/nvm>`_.

L'installation se fait simplement à l'aide de

.. sourcecode:: bash

    make zmd-install

ou, sous Windows (non testé):

.. sourcecode:: bash

    cd zmarkdown
    npm -g install pm2
    npm install zmarkdown --production
    cd ..


Utilisation
===========

Afin de pouvoir profiter de zmarkdown, vous devez lancer le serveur à l'aide de ``make zmd-start`` (ou, sous Windows, ``cd zmd/node_modules/zmarkdown && npm run server`` [non-testé]).
Vous pouvez vérifier qu'il est bien lancé à l'aide de ``zmd-check`` (qui ne fonctionne pas sous Windows).
On arrête le serveur en utilisant ``make zmd-stop``, ou bien ``pm2 kill``.
