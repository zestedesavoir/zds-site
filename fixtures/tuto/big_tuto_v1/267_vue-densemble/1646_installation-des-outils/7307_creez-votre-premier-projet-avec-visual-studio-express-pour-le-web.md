# L'interface de Visual Studio Express pour le Web

Nous allons vérifier que l'installation de Visual Studio Express pour le Web a bien fonctionné. Et pour ce faire, nous allons le démarrer et commencer à prendre en main ce formidable outil de développement.

Il y a une multitudes d'options mais c'est un outil très simple d'utilisation, si vous suivez ce tutoriel pas à pas, vous allez apprendre les fonctionnalités indispensables. Vous avez utilisé Visual C# pour faire vos applications en C# et maintenant vous utilisez Visual Studio Express pour le Web pour faire vos applications Web.

Visual C# et Visual Studio Express pour le Web possède des fonctionnalités communes. Commencez par démarrer l'IDE. Le logiciel s’ouvre sur la page de démarrage de Studio Express pour le Web :

->![Interface de Visual Studio Express pour le Web](/media/galleries/304/53d7b699-60f5-4a76-9e2e-089e6cbd07fa.png.960x960_q85.jpg)<-

# Nouveau projet

Je vous invite, seulement pour appréhender l'interface, à créer un projet Application Web ASP.NET MVC4 (voir figure suivante). Pour ce faire, trois solutions s'offrent à vous : cliquer sur le bouton **Nouveau projet**, se rendre dans le menu Fichier > Nouveau projet, ou utiliser le raccourci clavier ||Ctrl|| + ||n||.

->![Créer un nouveau projet](/media/galleries/304/5fcf2c36-ad10-40f4-9188-1f54d17f4d5d.png.960x960_q85.png)<-

Allez dans le nœud Web de Visual C# et sélectionnez Application Web ASP.NET. Tout comme avec Visual C#, vous avez la possibilité de changer le nom du projet et de changer le répertoire de l'application. Cliquons sur ||OK|| pour valider la création de notre projet. Vous remarquez que beaucoup plus de choses s'offrent à nous (voir figure suivante).

Dans cette fenêtre, il y a la liste des **modèles** de création de projets installés. Pour commencer, nous vous proposons de créer un modèle de type **application Web ASP.NET MVC**, nous reviendrons plus tard sur le terme MVC, retenez simplement que c'est une manière d'organiser son code.

->![Nouveau projet ASP.NET MVC](/media/galleries/304/9530afb5-899c-4241-a4ea-e985a611b6d3.png.960x960_q85.png)<-

Maintenant, il faut choisir avec quoi nous allons commencer notre application Web. ASP.NET propose plusieurs modèles :

- le projet **Vide** : comme son nom l'indique, nous créons un projet à partir de zéro, néanmoins Visual Studio y intégrera les références nécessaires vers les assemblies[^assemblies] ASP.NET, quelques bibliothèques JavaScript utiles pour une application Web ainsi qu'un fichier de configuration;
- le projet de **WebForms** : créer un projet ASP.NET Web Forms, basé sur les contrôles et le code évènementiel;
- le projet **MVC** : un projet tourné vers MVC, ce qui nous intéresse pour commencer;
- le projet **Web API** : une application Internet préconfiguré avec le contrôleur Web API. Nous aurons l'occasion de revenir dessus;
- le projet Application avec **une seule page**;
- le projet Application **Facebook**.

C'est beaucoup de modèles tout ça ! Alors lequel choisir ? Nous n'allons pas commencer à programmer directement, alors nous vous proposons de créer un projet **MVC** pour découvrir l'interface de Visual Studio pour le Web.

Sélectionnez MVC et laissez le reste tel quel, décochez la case en dessous **Windows Azure**. Validez avec ||OK||.

[[information]]
| **Windows Azure** est une plateforme d'hébergement Cloud Microsoft. Windows Azure nous permettra de publier une application Web, mais ça ne nous intéresse pas à ce stade du tutoriel.

->![](/media/galleries/304/7f5f3f00-add4-4e94-aa39-00d2159e1b28.png.960x960_q85.jpg)<-

Pas grand chose de différent comparé à Visual C# : nous retrouvons l'explorateur de solution avec toute l'organisation des fichiers et l'éditeur de code au milieu. Nous découvrons dans l'explorateur de solutions l'organisation des fichiers C# dans différents dossiers, ne vous attardez pas là-dessus car nous y reviendrons très vite.

[^assemblies]: Une assembly est un programme .NET qui a déjà été compilé. On les trouve souvent sous la forme de fichier `.dll`
