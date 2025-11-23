Il ne vous est jamais arrivé de faire une application en C# en vous disant : "Le code est vraiment mal organisé, mais bon au moins ça marche."

Trop de développeurs, et pas que les débutants, ne savent pas organiser leur code, ce qui peut par la suite poser des problèmes. En fait, il y a des problèmes en programmation qui reviennent tellement souvent qu'on a créé toute une série de bonnes pratiques que l'on a réunies sous le nom de **design patterns**. En français, on dit "patron de conception".

Le MVC est un design pattern[^designpat] très répandu. MVC est un acronyme signifiant **Modèle - Vue - Contrôleur**. Ce patron de conception, permet de bien organiser son code pour son application Web.
Le code est séparé en trois parties : la partir Modèle, la partie Vue et la partie Contrôleur. Les lecteurs attentifs auront remarqué que la solution de projet du projet que nous avons créée précédemment comportait trois répertoires portant ces noms :

->![Models, Views, Controllers](/media/galleries/304/2f5cdea5-dd3e-4526-b3c2-eef7fc76e7d9.png.960x960_q85.jpg)<-

Ci-dessous ce que nous trouvons dans chaque partie :

- **Modèle** : les modèles vont gérer tout ce qui est trait aux **données** de votre application. Ces données se trouvent en général dans une base de données. Les données vont être traités par les modèles pour ensuite être récupérées par les contrôleurs.

- **Vue** : comme son nom l'indique, une vue s'occupe... de l'affichage. On y trouve uniquement du code HTML, les vues récupère la valeur de certaines variables pour savoir ce qu'elles doivent afficher. Il n'y a pas de calculs dans les vues;

- **Contrôleur** : un contrôleur va jouer le rôle d'intermédiaire entre le modèle et la vue. le contrôleur va demander au modèle les données, les analyser, prendre des décisions et renvoyer le texte à afficher à la vue. Les traitements se font dans le contrôleur. Un contrôleur ne contient que du code en C# et réalise une **action**.

Résumons le tout schématiquement :

![modèle - données](/media/galleries/304/1f69d5c9-503c-4a36-9234-7f73fe6be230.png.120x120_q85_crop.jpg)

![vue - affichage](/media/galleries/304/edce0ef9-d6e9-4129-a075-66347923b547.png.120x120_q85_crop.jpg)

![contrôleur - action](/media/galleries/304/bd74f5f5-1efd-4b3e-b843-e8f0da4ff96d.png.120x120_q85_crop.jpg)

En suivant ce que nous avons écris plus haut, les éléments s'agencent et communiquent entre eux de cette façon :

->![Échange d'informations entre les éléments](/media/galleries/304/1a474da8-1d7e-4029-9872-7a2d0d3c2782.png)<-

Nous remarquerons que tout passe par le contrôleur : il va chercher les données dans le modèle, le modèle lui retourne ces données et enfin il transmet ces données à la vue. Lorsque qu'un visiteur demande une page Web depuis son navigateur, sa requête est dans un premier temps traitée par le contrôleur, seule la vue correspondante est retournée au visiteur.

[[information]]
| Pour rester simple, j'ai volontairement présenté un schéma simplifié. Une vraie application ASP.NET MVC fera intervenir des éléments supplémentaires.

MVC est une architecture vraiment souple et pratique mais quelque peu flou, lorsque nous commencerons à pratiquer en vous comprendrez mieux les rouages.

[^designpat]: Les patrons de conceptions sont nombreux, et participent surtout à la *programmation orientée objet*. Une grande partie d'entre eux a été détaillée par le [gang of four](http://geekswithblogs.net/subodhnpushpak/archive/2009/09/18/the-23-gang-of-four-design-patterns-.-revisited.aspx).
