[[i]]
| A partir de ce chapitre nous utiliserons Entity Framework comme ORM et nous suivrons l'approche *Code First*.

Entity Framework, c'est le nom de l'ORM officiel de .NET. Développé par Microsoft il est à l'heure actuelle en version 6. Vous pourrez observer l'arrivé d'une version mineure par semestre environ, parfois plus, parfois moins lorsque l'outil est très stable. Vous pouvez bien sûr le télécharger sur NuGet.

Je vous ai dit tout à l'heure qu'il fallait trois outils pour suivre l'approche *Code First*. Bien évidemment, Entity Framework les possède.

# Un *mapper*

Le mot francisé serait "mappeur", et son principal but est de faire correspondre les objets POCO à des enregistrements en base de données.

C'est à ce *mapper* que sont accrochés les *connecteurs* qui vous permettront d'utiliser les différents système de gestion de base de données. De base vous aurez droit à SQLServer LocalDB. Pour tester notre blog, c'est ce connecteur que nous utiliserons car il permet de créer rapidement des bases de données et de les supprimer tout aussi rapidement une fois qu'on a tout cassé ^^.

# Une API de description

Quand vous utilisez un ORM, il faudra parfois décrire les relations entre les classes. En effet, certaines sont complexes et peuvent être interprétées de plusieurs manière, il vous faudra donc dire explicitement ce qu'il faut faire.

Vous pouvez aussi vouloir nommer vos champs et tables autrement que ce que désire la *convention*.

Pour cela, vous avez deux grandes méthodes avec EntityFramework.

## Les annotations

Comme nous l'avions vu lorsque nous avons voulu vérifier la cohérence des données entrées par l'utilisateur, vous allez pouvoir décrire votre modèle avec des annotations.

Les annotations les plus importantes seront :

- `[Index]` : elle permet de s'assurer qu'une entrée est **unique** dans la table et grâce à ça accélérer fortement les recherches.
- `[Key]` : Si votre clef primaire ne doit pas s'appeler ID ou bien qu'elle est plus complexe, il faudra utiliser l'attribut Key
- `[Required]`: Il s'agit du même `[Required]` que pour les vues[^vue_modele], il a juste un autre effet : il interdit les valeurs `NULL` ce qui est une contrainte très forte.

[^vue_modele]: Nous pourrons d'ailleurs observer que tous les filtres par défaut sont utilisés à la fois par les vues et Entity Framework. C'est une sécurité supplémentaire et une fonctionnalité qui vous évitera de produire encore plus de code.

## La *Fluent API*

La seconde méthode a été nommée "Fluent API". Elle a été créée pour que ça soit encore une fois la production de code qui permette de décrire le modèle.

La Fluent API est **beaucoup plus avancée** en terme de fonctionnalité et vous permet d'utiliser les outils les plus optimisés de votre base de données.

Je ne vais pas plus loin dans l'explication de la Fluent API, nous ne l'observeront à l'action que bien plus tard dans le cours, lorsque nous aurons affaire aux cas complexes dont je vous parlais plus tôt.

# Les migrations *Code First*

Troisième et dernier outil, qui aura sont propre chapitre tant il est important et puissant.

Les migrations sont de simple fichier de code (on ne vous a pas menti en disant que c'était du Code First) qui expliquent à la base de données comment se mettre à jour au fur et à mesure que vous faîtes évoluer votre modèle.

Une migration se termine toujours par l'exécution d'une méthode appelée `Seed` qui ajoute ou met à jour des données dans la base de données soit pour **tester** soit pour créer un environnement minimum (exemple un compte administrateur).
