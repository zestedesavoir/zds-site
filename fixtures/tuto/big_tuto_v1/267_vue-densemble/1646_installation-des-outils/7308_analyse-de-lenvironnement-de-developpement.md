Nous allons éplucher l'interface de Visual Studio pour parler de quelques éléments. Le fait que vous avez déjà touché au langage C# ou VB.NET vous permet de connaître quelques éléments de l'interface, comme l'explorateur de solutions, l'éditeur ou la barre d'outils. Regardons maintenant comment va s'organiser Visual Studio pour un projet d'application Web.

### L'organisation de Visual Studio

Sachez avant tout que Visual Studio permet de faciliter la vie du développeur. Sa capacité de pouvoir se personnaliser facilement en fait de lui un outil très personnel au développeur.

Nous allons commencer par parler de l'**explorateur de solutions**. C'est un outil intégré à Visual Studio qui présente les fichiers relatifs aux projets rattachés à la solution courante. Le plus souvent, nous ouvrons nos fichiers par un double clic. Visual Studio utilise des fichiers spécifiques pour gérer les solutions (extensions `.sln` et `.suo` pour les options utilisateurs) et les projets (`.csproj`).

![L'explorateur de solutions Visual Studio](/media/galleries/304/f51615bb-a898-457f-bf66-44a611953b99.png.960x960_q85.jpg)

Un deuxième outil souvent important est la **barre de propriétés** : elle permet d'afficher et d'éditer les propriétés d'un objet sélectionné, comme un fichier de l'explorateur de solutions.

![Barre de propriétés](/media/galleries/304/03a265b8-af15-4ebd-b694-5477dd9a0dd0.png.960x960_q85.jpg)

Enfin, nous allons parler d'un dernier outil important à nos yeux : l'**explorateur de serveur**. Le plus souvent, l'explorateur de serveurs est utilisé pour accéder aux bases de données nécessaires au fonctionnement d'une application. Il donne aussi des informations sur l'ordinateur courant telles que les états Crystal report, les logs, les services Windows, etc.

![Explorateur de serveurs](/media/galleries/304/43cf5cc6-7930-41b5-b345-5ff9dd72d02d.png.960x960_q85.png)

[[information]]
| Si vous ne voyez pas ces fenêtres chez vous, vous pouvez les rendre visible en allant dans le menu **Affichage** de Visual Studio.

L'élément le plus important reste l'éditeur de code qui offre une colorisation de syntaxe, un auto-complétion et un soulignage d'erreurs dans le code.

![Fonctionnalités de l'éditeur](/media/galleries/304/0c73bb2f-7354-40ef-a971-77289e34e9a9.png.960x960_q85.jpg)

### Obtenir des informations complémentaires en cas d'erreur

Lorsque vous voulez corriger un bug, le plus souvent vous aller utiliser le débuggeur pas à pas de visual studio.

Néanmoins il peut y avoir des cas - rares, mais existants- où le débuggeur ne suffira pas et où vous aurez besoin de plus d'informations.

Pour cela, il faut aller regarder le *journal* du serveur. Ce dernier se trouve dans le dossier `Mes Documents\IISExpress\TraceLogFiles` et `Mes Documents\IISExpress\logs`.
Leur allure vous rebutera peut être, mais ils vous permettront de voir, tel que le serveur le voit, comment votre site s'est exécuté.

Si vous avez un jour un problème et que sur le forum quelqu'un vous demande les logs, c'est là qu'il faut aller les chercher.
