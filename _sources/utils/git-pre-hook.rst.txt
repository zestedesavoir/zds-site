===================================================
Détection automatique des erreurs *flake8* avec Git
===================================================

Afin de s'assurer qu'aucune erreur de mise en forme ne passe les commits,
il peut être utile de rajouter un hook de pre-commit à git. Un hook est un petit
programme qui sera exécuté avant une action particulière de git. En l'occurence nous
allons rajouter un hook qui s'executera juste avant la validation d'un commit.

Pour cela, commencer par créer et éditer le fichier `.git/hooks/pre-commit`

Ensuite, il ne reste plus qu'à rajouter le contenu suivant dans ce fichier et dorénavant
le controle flake (pour le respect PEP) sera exécuté avant la validation du message de commit.
Ainsi, plus aucune erreur flake ne viendra vous embêter à posteriori et la base de code
restera propre et lisible au cours du temps !

.. sourcecode:: bash

    #!/bin/sh

    flake8 zds

    # Store tests result
    RESULT=$?

    [ $RESULT -ne 0 ] && exit 1
    exit 0


Enfin n'oubliez pas de le rendre executable via chmod

.. sourcecode:: bash

    chmod +x .git/hooks/pre-commit
