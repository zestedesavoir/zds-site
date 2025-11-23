Maintenant, il est temps de voir le rendu de l'application Web sur navigateur. Il ne suffit pas de cliquer sur un fichier HTML comme vous avez l'habitude de la faire, mais avant tout de **générer** le projet. Cette phase permet de compiler le code côté serveur, le C#.

Allez dans le menu Déboguer et cliquez sur Démarrer le débogage ou appuyez directement sur la touche ||F5|| de votre clavier.

->![Fenêtre de sortie](/media/galleries/304/091618ff-0bc3-4696-ae24-1d42e0bfb1f5.png.960x960_q85.jpg)<-

Remarquez qu'un fichier dll est généré en sortie.

Ensuite, Visual Studio va démarrer **IIS Express**, qui est une version allégé de IIS. C'est le logiciel de serveur de services Web permettant d'exécuter une application ASP.NET. Visual Studio démarre ensuite le navigateur Web et dirige automatiquement vers la page d'accueil. La page web que vous voyez à l'écran vous a été envoyée par votre propre serveur IIS Express que vous avez installé en même temps que Visual Studio Express pour le Web. Vous êtes en train de simuler le fonctionnement d'un serveur web sur votre propre machine. Pour le moment, vous êtes le seul internaute à pouvoir y accéder. On dit que l'on travaille en local. Notons que l'URL affichée par le navigateur dans la barre d'adresse est de la forme **http://localhost:#numero de port/**, ce qui signifie que vous naviguez sur un site web situé sur votre propre ordinateur.

Lorsque Visual Studio exécute une application Web, il génère un numéro de port permettant de faire fonctionner l'application.

->![](/media/galleries/304/f0ef70f7-68da-4a1b-b86f-a7db8d005afb.png.960x960_q85.png)<-

Nous pouvons ensuite nous balader sur les différents liens qu'offre l'application toute prête. Notons qu'en fonction de la taille de votre fenêtre, les éléments sont agencés différemment.

->![rendu sur navigateur grand format](/media/galleries/304/b7785c2b-97ea-474b-8e0a-628e7ce14576.png.960x960_q85.png)<-

->![rendu sur navigateur petit format](/media/galleries/304/af632495-7ea2-4722-b8ed-ceb82c341743.png.960x960_q85.png)<-

Ainsi le menu se retrouve soit directement sur la page de l'application, soit dans un menu déroulant.
L'application propose aussi un support de connexion et d'enregistrement implémenté. Lorsque nous créerons notre application, nous partirons de zéro. Ce projet tout fait vous permet d'avoir un avant-gout de ce que nous pouvons faire avec ASP.NET.
