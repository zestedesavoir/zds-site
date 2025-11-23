=========================
Installation sous Windows
=========================

Pour installer une version locale de ZdS sur Windows, il est recommandé
d'utiliser `le sous-système Linux
<https://learn.microsoft.com/en-us/windows/wsl/install>`_, et `installez Zeste
de Savoir comme si vous étiez sur la distribution choisie
<install-linux.html>`__.

- Exemple pour le sous système Ubuntu
    .. sourcecode:: bash

        sudo apt install build-essential git
        git clone https://github.com/<votre-pseudo>/zds-site
        cd zds-site
        ./scripts/install_zds.sh -packages ubuntu


L'installation directement sur Windows n'est pas supportée.
