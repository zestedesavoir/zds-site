Historiquement parlant, WebForm est la technologie qui a fait connaître ASP.NET.

Pour autant, les WebForms sont en perte de vitesse face à l'utilisation de MVC et des API REST.

Le MVC pour le web a trouvé ses lettres de noblesse dans bien des langages tels que Java, PHP ou ruby. Les procédures utilisées sont donc assez standardisées, ce qui facilite la maintenance et l'arrivée de nouveaux développeurs sur un projet. Pratique, par exemple, si vous désirez partager votre code sur [github](https://github.com) comme le fait [ZDS](https://github.com/zestedesavoir/zds-site) !

MVC permet une réelle **efficacité** lorsque vous codez, ASP.NET vous proposant déjà beaucoup de package déjà prêts à être utilisés via *nuget*.

La popularité de MVC est surtout due à une chose : lorsque vous êtes sur un site internet les actions que vous réalisez sont découpées de manière à répondre toujours à ce schéma :

création->validation->enregistrement->affichage->modification->validation->enregistrement->affichage.

Imaginons que nous avons un blog.
En tant qu'auteur, nous voulons ajouter des articles.

1. Alors nous allons **créer** cet article ;
2. Puis le programme va vérifier qu'il est correct (par exemple : le titre est-il renseigné?) ;
3. Puis nous allons l'afficher pour pouvoir le lire ;
4. Nous allons vouloir corriger nos fautes d'orthographe et donc nous allons modifier ;
5. Une nouvelle fois, le programme vérifie qu'on n'a pas fait de bêtises ;
6. Et on affiche la version corrigée.
