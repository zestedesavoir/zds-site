====================================
Création d'un jeu de données de test
====================================

Afin de vous permettre de tester rapidement l'application zeste de savoir, nous mettons à votre disposition un jeu complet de données de test.
Ces données sont à séparer en deux types :

- les données totalement sérialisables (les utilisateurs, les forums, les catégories...)
- les données qui nécessitent un traitement lors de leur création (indexation git des tuto, import d'image des galleries...)

Chacun des jeux de données est géré par deux outils différents :

Les fixtures django
===================

Pour les données totalement sérialisables, nous utilisons la commande `python manage.py loaddata` de django.
Cette commande prend des fichiers yaml en entrée et crée les données ainsi sérialisées.
Le format est documenté sur le site officiel de django.

Les fixtures ad hoc
===================

Certaines données nécessitent des traitement complexes avant d'être utilisables et donc ne peuvent être plainement sérialisées et utilisées par l'outil de django.
Pour cela, nous avons mis en place un script qui permet d'utiliser les factories pour créer ces objets et y appliquer les traitements nécessaires.

Pour utiliser les fixtures de ce type, il vous suffira de lancer le script `python load_factory_data.py fichier_fixtures.yaml`.

Tout comme l'outil django, nous utilisons yaml pour configurer les données, le format d'une fixture sera celui-ci

.. sourcecode:: yaml

    -   factory: nom_factory
        fields:
            champ1: "valeur1"
            champ2: "valeur2"
            champN: "valeurN"
