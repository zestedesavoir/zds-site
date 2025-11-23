# Cas d'utilisation

Comme nous avons pris de bonnes habitudes, pour définir ce qu'est une migration, partons d'un cas concret.

Vous avez pu voir jusqu'à présent qu'à chaque fois que vous amélioriez votre modèle de données, il fallait remettre la base de données à zéro.
Je ne sais pas pour vous, mais, moi, je n'ai pas envie de devoir remettre mon blog à zéro à chaque fois que je l'améliore.

Alors on peut tenter de jouer avec des sauvegardes. Avant d'améliorer le site, je sauvegarde ma base de données sur une copie. Ensuite, je vais faire le changement et enfin je vais migrer mes données sur la base de données qui vient d'être recréée.

Vous comprenez que c'est long et frustrant.

Mais en plus de ça, j'ai un ami qui m'aide à créer mon blog, alors lui aussi, de temps en temps il fait des améliorations sur le modèle de données. Malheureusement, à chaque fois, je ne m'en rend pas tout de suite compte alors je perds beaucoup de temps à tout recréer.

Et puis parfois, comme mon ami est très en retard par rapport aux modifications que j'ai faites, il y a tellement de choses qui changent qu'il oublie de faire certaines configurations et donc ça plante.

Enfin, mon ami, il s'y connaît en base de données, son livre de chevet, c'est [ce tuto](http://openclassrooms.com/courses/administrez-vos-bases-de-donnees-avec-mysql), alors pour lui les vues, les déclancheurs, les index... ça n'a plus aucun secret. Mais a priori, votre code ne dit pas comment utiliser ces fonctionnalités des systèmes de gestion de base de données.

# La solution : les migrations

Désireux de trouver un remède à tous ces problèmes les différents framework web ont travaillé sur un concept qu'on appelle les **migrations
**. L'avantage, c'est ASP.NET ne fait pas exception à la règle.

Une migration, c'est un outil qui résoud ces problèmes en fonctionnant ainsi :

- A chaque changement du modèle, on crée le code SQL qui permet de *modifier à chaud* la base de données;
- L'exécution de ce code est totalement automatisé;
- Chaque code possède un marqueur temporel qui permet d'ordonner les migrations.

Schématiquement, on pourrait dire que les migrations fonctionnent ainsi :

![Fonctionnement des migration](/media/galleries/304/107720ff-9904-4b47-9b51-d5c810690412.png.960x960_q85.jpg)

L'avantage de ce système c'est que non seulement il facilite tout, mais surtout il se base sur des simples fichiers de code, dans notre cas du C#. Du coup, vous pouvez modifier le comportement de vos migration pour améliorer votre BDD. Nous allons voir ça par la suite.

Enfin, autre fait intéressant : si à force de faire beaucoup de modifications, vous trouvez que votre modèle n'est pas aussi bon que vous le souhaitez, toutes les migrations sont réversibles. Une fois le `reverse` opéré, il ne vous reste plus qu'à supprimer le fichier de migration et plus personne ne se souviendra que vous avez tenté de faire ces modifications là et avez échoué.

# Mettre en place les migrations

Comme on parle de tâches automatiques, il ne faudra pas avoir peur du terminal, enfin je veux dire de **PowerShell**.

Dans le menu "Outils" puis "Gestionnaire de package NuGet", sélectionnez "Console du gestionnaire de paquet".

Là, il vous faudra entrer la commande `Enable-Migrations` puis lancer la commande `Add-Migration initial`.

Plus tard, quand vous désirerez ajouter une migration, il faudra utiliser la commande `Add-Migration nom_lisible_par_un_humain_pour_la_migration`. Ensuite, la commande magique s'appellera `Update-Database`.

Dans cette vidéo, nous ferons un tour du propriétaire des migrations :

->!(https://www.youtube.com/watch?feature=player_embedded&v=Co0pi4hsZPg)<-
