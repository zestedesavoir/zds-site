Nous désirons créer un site web. Ce site web va devoir stocker des données. Ces données ont des relations entre elles...

Bref, nous allons passer par une base de données. Pour simplifier les différentes questions techniques, nous avons fait un choix pour vous : nous utiliserons une base de données **relationnelle**, qui se base donc sur le SQL.

Maintenant que ce choix est fait, il va falloir s'atteler à la création de notre base de données et à la mise en place de notre ORM.
Comme ce tutoriel utilise Entity Framework, nous utiliserons les outils que Microsoft met à notre disposition pour gérer notre base de données avec cet ORM précis.

Avant toute chose, je voulais vous avertir : une base de données, quelle que soit l'approche utilisée, ça se réfléchit au calme. C'est souvent elle qui déterminera les performances de votre application, la créer à la va-vite peut même tuer un petit site.

Maintenant, entrons dans le vif du sujet et détaillons les trois approches pour la création d'une base de données.

# L'approche *Model First*

L'approche *Model First* est une approche qui est issue des méthodes de [conception classique](http://fr.wikipedia.org/wiki/M%C3%A9thodes_d%27analyse_et_de_conception). Vous l'utiliserez le plus souvent lorsque quelqu'un qui a des connaissances en base de données, notamment la méthode MERISE[^merise].

Cette approche se base sur l'existence de diagramme de base de données parfois appelés *Modèle Logique de Données*. Ces diagrammes présentent les entités comme des classes possédant des attributs et notamment une *clef primaire* et les relient avec de simples traits.

Pour en savoir plus sur cette approche, je vous propose de suivre cette petite vidéo :

->!(http://youtu.be/aGUhBt1Cf9M)<-
# L'approche *Database First*

Comme son nom l'indique, cette méthode implique que vous créiez votre base de données de A à Z en SQL puis que vous l'importiez dans votre code. C'est une nouvelle fois le *Modèle Logique de Données* qui fera le lien entre la base de données et l'ORM. La seule différence c'est que cette fois-ci c'est Visual Studio qui va générer le schéma par une procédure de *rétro ingénierie*.

# L'approche *Code First*

Cette dernière approche, qui est celle que nous avons choisi pour illustrer ce tutoriel, part d'un constat : ce qu'un développeur sait faire de mieux, c'est coder.

Cette approche, qui est la plus commune dans le monde des ORM consiste à vous fournir trois outils pour que vous, développeur, n'ayez qu'à coder des *classes* comme vous le feriez habituellement et en déduire le modèle qui doit être généré.

Nous avons donc de la chance, nous pourrons garder les classes que nous avions codées dans la partie précédentes, elles sont très bien telles qu'elles sont.

[[q]]
|Trois outils, ça fait beaucoup non? Et puis ces quoi ces outils?

Quand vous aller définir un modèle avec votre code vous allez devoir passer par ces étapes :

1. Coder vos classes pour définir le modèle
2. Décrire certaines liaisons complexes pour que le système puisse les comprendre
3. Mettre à jour votre base de données
4. Ajouter des données de tests ou bien de démarrage (un compte admin par exemple) à votre base de données.

Et cela, ça demande bien trois outils. Heureusement pour vous, ces outils sont fournis de base dans Entity Framework, et nous en parlons dans le point suivant, soyez patients ;)

# Comment choisir son approche

Quand vous démarrez un projet, vous allez souvent vous poser beaucoup de questions. Dans le cas qui nous intéressent, je vous conseille de vous poser trois questions :

- Est-ce qu'il y a **déjà** une base de données? Si oui, il serait sûrement dommage de tout réinventer, vous ne croyez pas?
- Est-ce que vous êtes seuls? Si oui, vous faites **comme vous préférez**, c'est comme ça que vous serez le plus efficace, mais si vous êtes à plusieurs il vous faudra vous poser une troisième question primordiale :
- Qui s'occupe de la BDD : un codeur ou un expert qui a réfléchi son modèle sur un diagramme? Il y a fort à parier que s'adapter à l'expertise de la personne qui gère la BDD est une bonne pratique, non?

Pour être plus visuel, on peut dire les choses ainsi : 


![Choix de l'approche](http://zestedesavoir.com/media/galleries/304/4eca47a4-852f-4b64-8a64-aee222c95513.png.960x960_q85.jpg)


[^merise]: La [Méthode MERISE](http://fr.wikipedia.org/wiki/Merise_%28informatique%29) est une méthode franco-française encore très répendue aujourd'hui pour gérer [les projets](http://www.addstones.com/cycle-de-vie-d-un-projet) et notamment les étapes de conception.