========================
Installation dans Docker
========================


.. note::

    Par manque de développeurs utilisant Docker au sein de l'équipe de
    développement de ZdS, cette section n'est guère fournie. Les instructions
    données ici ne le sont qu'à titre indicatif. N'hésitez pas à signaler tout
    problème ou proposer des améliorations !

L'installation de l'environnement de développement dans Docker se base sur `l'installation sous Linux <install-linux.html>`_.

Lancez un shell interactif dans un conteneur basé sur Debian :

.. sourcecode:: bash

    docker run -it -p 8000:8000 debian:bookworm


Une fois dans le conteneur, saisissez les commandes suivantes :

.. sourcecode:: bash

    # On se place dans le $HOME
    cd

    # Permet d'utiliser correctement apt
    DEBIAN_FRONTEND=noninteractive

    # Installez les paquets minimaux requis
    apt update
    apt install sudo make vim git

    # Clonez le dépôt de ZdS
    git clone https://github.com/<votre login>/zds-site.git
    cd zds-site/

    # Installez ZdS
    make install-linux

    # Nécessaire pour avoir nvm dans le PATH
    source ../.bashrc

    # À partir de maintenant, les commandes ne sont plus spécifiques à l'utilisation de Docker.

    # Lancement de ZdS
    source zdsenv/bin/activate
    make zmd-start
    make run-back
