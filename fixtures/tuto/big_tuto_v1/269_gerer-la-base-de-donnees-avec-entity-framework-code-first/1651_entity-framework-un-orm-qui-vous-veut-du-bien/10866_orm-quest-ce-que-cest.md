# Principe d'un ORM

Comme dit en introduction, ORM signifie que l'on va traduire de l'Objet en Relationnel et du Relationnel en Objet.

[[q]]
|Mais dans cette histoire c'est quoi "objet" et "relationnel"?

Le plus simple à comprendre, c'est "l'objet". Il s'agit ici simplement des classes que manipule votre programme. Ni plus, ni moins.

Par exemple, dans notre blog nous avons des articles, donc nous avons créé une classe `Article` qui décrit ce qu'est un article du point de vue de notre programme. Chouette, non?

Maintenant, le gros morceau : le "Relationnel".

Nous ne parlons pas ici des relations humaines, ni même des relations mathématiques mais de la *représentation relationnelle des données*.

Ce terme vient de l'histoire même des bases de données[^bdd_histoire]. Ces dernières ont été créées pour répondre à des principes complexes[^acid] et une logique ensembliste.
De ce fait, les créateurs des bases de données, notamment [M.Bachman](http://fr.wikipedia.org/wiki/Charles_Bachman) vont créer une architecture qui va représenter les données en créant des *relations* entre elles.

Plus précisément, les données vont être *normalisées* sous forme **d'entités** qui auront entre elles trois types d’interactions : One-To-One, One-To-Many, Many-To-Many.
Nous verrons la traduction de ces termes au cours de nos cas d'étude.

Plus tard, avec l'arrivée de la programmation orientée objet, les chercheurs dans le domaine des bases de données, vont tenter de modéliser d'une manière compatible avec UML le fonctionnement des bases.

Grâce à ces travaux les programmes ont pu traduire de manière plus immédiate les "tables de données" que l'on trouve dans les bases de données relationnelles en instances d'objets.

Dans le cadre de .NET l'ORM est souvent constituer d'une API qui se découpe en deux parties : un gestionnaire d'objet/données et un "traducteur" qui se sert de Linq To SQL.

Grâce à cette organisation, l'ORM n'a plus qu'à se brancher aux connecteurs qui savent converser avec le système choisi (MSSQL, MySQL, Oracle, PostGreSQL...).

->![Fonctionnement d'un ORM](/media/galleries/304/82eb4b9b-3692-44d1-910d-5f80aa103ac8.png.960x960_q85.jpg)<-


# Des alternatives à Entity Framework?

Comme vous l'aurez compris, nous allons choisir *Entity Framework* en tant qu'ORM pour plusieurs raisons :

- c'est le produit mis en avant par Microsoft, il est régulièrement mis à jour (actuellement : version 6);
- il est bien documenté;
- il est parfaitement intégré au reste du framework .NET (validation, exceptions, Linq...);
- il se base sur l'API standard [ADO.NET](http://msdn.microsoft.com/fr-fr/library/h43ks021%28v=vs.110%29.aspx);
- il est complet tout en restant suffisamment simple d'utilisation pour le présenter à des débutants.

Comme nous avons pu nous en rendre compte dans les parties précédentes, ASP.NET ne nécessite pas un ORM.
C'est juste un outil qui vous facilitera le travail et surtout qui vous assurera une véritable indépendance d'avec le système de gestion de bases de données que vous utilisez.

Le monde du .NET est néanmoins connu pour fournir un nombre important d'alternatives au cours du développement.
Une petite exploration des dépôts NuGet[^list_orm_nuget] vous permettra de vous en rendre compte.

Il existe en gros deux types d'ORM :

- Les ORM complets, qui accèdent vraiment au meilleurs des deux mondes objet et relationnels. Entity Framework en fait partie;
- Les ORM légers, qui sont là pour vous faciliter uniquement les opérations basique du CRUD


## Un ORM Complet : NHibernate

[NHibernate](http://izlooite.blogspot.fr/2011/04/nhibernate-good-bad-and-ugly-that-it.html) est un ORM qui se veut être le concurrent direct de Entity Framework.

Son nom est un mot valise rassemblant ".NET" et "Hibernate".
Il signifie que NHibernate est le portage de l'ORM Hibernate, bien connu des utilisateurs de Java en .NET.

De la même manière que Entity Framework, NHibernate se base sur ADO.NET.
Par contre, il reprend un certain nombre de conventions issues du monde Java comme l'obligation de posséder un constructeur par défaut.

## Un ORM Léger : PetaPOCO

[PetaPOCO](https://github.com/toptensoftware/petapoco) est un ORM qui s'est construit par la volonté grandissante des développeurs à utiliser des *POCO*.

POCO, c'est un acronyme anglais pour Plain Old CLR/C# Object, autrement dit, un objet qui ne dépend d'aucun module externe.

Le problème posé par les ORM tels que NHibernate et EntityFramework, c'est que rapidement vos classes de modèles vont s'enrichir d'annotations, d'attributs ou de méthodes qui sont directement liés à ces ORM.

Or, en informatique, on n'aime pas que les classes soient fortement couplées, on essaie au maximum de respecter le principe de responsabilité unique ([SRP](http://www.oodesign.com/single-responsibility-principle.html)).

Nous verrons plus tard que dès que l'accès à la base de données est nécessaire, nous préférons utiliser le patron de conception [Repository](http://chamamo.wordpress.com/2013/08/08/le-pattern-repository-en-c/).
L'utilisation d'un ORM complet peut rapidement mener à des *repository* assez lourds à coder et à organiser.

PetaPOCO vous permet donc d'utiliser vos classes de modèle tout simplement. Par contre certaines fonctionnalités ne sont pas implémentées.

[^bdd_histoire]: [wikipédia](http://fr.wikipedia.org/wiki/Base_de_donn%C3%A9es#Histoire)
[^list_orm_nuget]: [liste complète des ORM publiés sur NuGet](https://www.nuget.org/packages?q=ORM)
[^acid]: Les bases de données sont [ACID](http://www.journaldunet.com/developpeur/tutoriel/theo/060615-theo-db-acid.shtml).
