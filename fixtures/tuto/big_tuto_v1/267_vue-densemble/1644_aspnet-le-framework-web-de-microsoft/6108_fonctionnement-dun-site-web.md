Lorsque vous avez appris à utiliser HTML et CSS, vous avez appris à créer des pages que le navigateur sait comprendre. Le problème, c'est qu'elles sont fixes et c'est pour cette raison que vous êtes en train de lire ce tutoriel.

Prenons un page web de  base codé en HTML : son contenu n'évolue uniquement que si vous touchez **vous même** au code source. Faire un blog, un site d'actualité, un comparateur de prix risque d'être très difficile uniquement en HTML. Sans compter qu'il faudra le mettre constamment à jour et de le maintenir.

Ainsi nous pouvons différencier deux types de sites web : les **sites statiques** et les **sites dynamiques**. Les sites statiques sont donc bien adaptés pour réaliser des sites dit "vitrine", pour présenter par exemple son entreprise ou son CV, mais sans aller plus loin. Ce type de site se fait de plus en plus rare aujourd'hui, car dès que l'on rajoute un élément d'interaction (comme un formulaire de contact), on ne parle plus de site statique mais de site dynamique.

A l'inverse de cela, un site dynamique propose une interaction avec le visiteur.
Zeste de savoir est un exemple de site dynamique. Le forum, par exemple change de contenu tous les jours de manière automatique, à chaque fois qu'un membre poste quelque chose.

Créer un site dynamique est un peu plus complexe dans le sens où  il faut utiliser des technologies supplémentaires que le HTML et CSS qui, elles, s'exécuteront sur ce qu'on appelle un serveur. ASP.NET en est une.

Lorsque les utilisateurs viennent sur un site codé avec ASP.NET, ils envoient une requête au **serveur**.
Ce dernier, comprend la requête, fait des calculs, va chercher des données dans la base de données ou dans d'autres services (ex : Wikipédia, Twitter) et **crée** une page HTML.

Cette page HTML est alors envoyée au client, qui peut la lire. Le client ne verra jamais du code exécuté sur le serveur.
Le code C# va demander de générer cette page HTML. Plus précisément, c'est le rôle de ce qu'on appelle les **vues**.

[[information]]
| Sur n'importe quel site il est possible pour le visiteur de voir le code HTML de la page. En général cela ce fait via le raccourci de touches ||Ctrl|| + ||u||.

### Fonctionnement d'un site dynamique

Voici un schéma résumant le fonctionnement d'un site Web dynamique :

-> ![client-serveur](/media/galleries/304/4829bf9c-c9b7-4b36-8096-d4fca094c155.png.960x960_q85.jpg)
Figure: L'architecture client/serveur
 <-

La page web est générée à chaque fois qu'un client la réclame. C'est précisément ce qui rend les sites dynamiques vivants : le contenu d'une même page peut changer d'un instant à l'autre.

Le **client** envoie des requêtes au serveur. C'est le **serveur**, via ASP.NET, qui fait tout le boulot via également des requêtes :

- Chercher des données dans une base de données, par exemple le dernier message que vous avez posté ;
- Chercher des données dans des flux externes, par exemple le nombre de followers de votre dernier article via Twitter;

Le tout est ensuite renvoyé au serveur, qui lui même renvoie au client sous forme de page web HTML complète.
