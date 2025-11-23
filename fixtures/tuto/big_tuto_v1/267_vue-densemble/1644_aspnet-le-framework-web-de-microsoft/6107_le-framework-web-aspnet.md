Passons à la partie qui nous intéresse le plus : **ASP.NET**. ASP.NET est un ensemble de technologies tournées vers le Web créé par Microsoft. Il est utilisé pour dynamiser les sites Web.

[[information]]
| ASP.NET est principalement supporté par **Windows**. C'est pourquoi la suite du tutoriel se basera sur un environnement de développement Windows. Néanmoins, grâce à [mono](http://www.mono-project.com/), il est possible d'héberger le site sur un serveur linux.

Avant de lire la suite, il faut savoir quelques petites choses. Lorsque vous surfez sur le Web, il y a deux acteurs :

- Le **client** : c'est vous. En lisant ce tutoriel, vous êtes client donc visiteur de la page Web.
- Le **serveur** : ce sont des ordinateurs puissants qui stockent et délivrent des pages web aux internautes, c'est-à-dire aux clients.

-> ![Le client et le serveur](/media/galleries/304/e92474d5-2ed6-45b5-be7a-16d65c582f43.png.960x960_q85.png) <-

Passons à la suite. Le nom du framework est divisé en deux parties **ASP** et **.NET**. Analysons cela :

La première partie (ASP) est un acronyme de **A**ctive **S**erver **P**ages et symbolise le fait que le framework est un fournisseur de services applicatifs. Nous voyons dans l'acronyme le fait que pour dynamiser les pages HTML d'un site Web, il faut qu'il y ait du code logique côté serveur.

[[attention]]
| Attention à ne pas confondre ASP.NET et ASP : ce sont deux technologies différentes provenant du même éditeur. ASP est une technologie beaucoup plus vieille.

Et enfin la seconde partie signifie qu'il est basé sur **.NET**, la technologie phare de Microsoft.
ASP.NET inclut la génération du code HTML du code côté serveur, l'utilisation de la programmation orientée objet et des bibliothèques du Framework .NET.

[[information]]
|A noter que ASP.NET offre de bonnes performances du fait que votre programme est *compilé*.
|Lorsque vous envoyez votre code sur le serveur, celui-ci reçoit un fichier *exécutable* et que le compilateur a déjà optimisé.
|Cela permet d'avoir une exécution accélérée comparée à des langages comme python ou PHP.

-> ![](/media/galleries/304/fe70d3e4-56a1-4cf4-a6be-a7981b7a14c4.png.960x960_q85.png) <-

Lorsque le client va demander une page web, le moteur d'ASP.NET va décider quelle est l'**action** à effectuer, l'exécuter et générer la page HTML à partir des données traitées par l'action.

ASP.NET est un framework qui vous offrira énormément de possibilités pour créer des applications web. Ci-dessous un schéma montrant les différentes couches de ASP.NET.

-> ![](/media/galleries/304/49edeb53-0d2a-4eba-b981-cf3afbd9e38e.png.960x960_q85.jpg)
Figure: Les possibilités d'ASP.NET <-

Le gros avantage d'ASP.NET, c'est qu'il se repose sur le framework .NET, ce qui lui donne accès à tout ce
que .NET a de mieux à vous offrir. Citons par exemple l'accès aux données, les tests unitaires, linq to SQL, etc.

Nous découvrirons dans les chapitres suivants les deux dernières couches qui composent ASP.NET, à savoir ce qui concerne les Web Forms, les Web Pages et MVC.
