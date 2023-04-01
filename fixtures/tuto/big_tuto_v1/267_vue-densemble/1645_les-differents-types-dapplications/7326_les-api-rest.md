# Définition de API REST

API REST... Deux acronymes l'un à côté de l'autre et qui occupent une place extrêmement importante dans le web actuel.

API, cela signifie "interface pour programmer des applications". Basiquement, c'est un ensemble de fonctions qui vous permettent -dans le meilleur des cas- de faire très facilement des opérations souvent complexes.

Par exemple, lorsque vous utilisez LINQ, vous utilisez une API composée de tout à tas de fonctions telles que `Select` ou `Where`.
Le mot API n'est donc pas immédiatement lié au Web. Pourtant, vous entendrez de temps en temps parler d'API Wikipédia, Twitter, IMDB... Et eux, ce sont des sites web.

Le principe de base d'une API Web, c'est de dire que votre site devient un *service* et donc en envoyant une requête vous pourrez obtenir les données que ledit service accepte de vous donner. Cela peut être le contenu d'une page wikipédia par exemple.

Le gros avantage de ce service, c'est qu'il ne vous fournit plus une page HTML avec tout le design associé mais uniquement le contenu. Ce qui permet d'accélérer globalement les choses, puisque s'il n'y a que le contenu, il y a moins de choses à télécharger, moins de choses à interpréter...

L'idée d'un service web n'est pas neuve. Il y a encore quelques années, un modèle de service était très à la mode : SOAP.
Ce dernier s'appuyait uniquement sur le XML et certaines entêtes HTTP pour fournir un service aux utilisateurs. C'est aussi un système assez complexe qui s'adapte mal au web.
S'il n'a pas été aussi plébiscité que les API REST, c'est simplement qu'il était trop complexe à utiliser pour ceux qui voulait se servir des données du service. En plus le XML c'est relativement lourd, en effet il faut écrire beaucoup de code pour exprimer des choses même basiques.

Puis le javascript est devenu célèbre. Et avec lui le JSON. Un format très léger et qui permet de transporter des données de manière simple et rapide.

L'idée de REST est d'allier la légèreté de JSON (bien qu'il soit compatible avec XML) pour transmettre facilement la représentation des données tel que le service sait les manipuler.
Comme il n'y a qu'un simple "transfert de données", l'utilisation de REST va être simplifié grâce à l'utilisation de simples URL comme l'adresse du site. Seule la **méthode HTTP** permettra de différencier l'action à faire.

Par exemple, le site [Zeste De Savoir](http://zestedesavoir.com) propose une API REST qui permet à certains développeurs de créer des applications mobiles par exemple. Lors qu'un utilisateur de ces applications envoie un message sur les forums, il envoie une requête **POST** avec une ressource "message" qui contient le texte de son message et l'identifiant du sujet. De même lorsqu'il veut afficher les forum, il envoie une requête **GET** avec l'identifiant du forum ou du sujet à afficher.

# Faire une API REST avec ASP.NET

Le *template* `Web API` de ASP.Net ressemble énormément à un site MVC.

->![Architecture d'un projet API](/media/galleries/304/59caa435-e9d5-40b4-982b-64a737df10f5.png.960x960_q85.png)<-

La raison est simple : vous allez utiliser du MVC sauf qu'au lieu d'avoir des vues, le contrôleur renverra juste du JSON ou du XML selon votre configuration.

[[question]]
| S'il n'y a pas de vue, pourquoi il y a un dossier vue?

Une API doit être utilisée par des programmeurs pour faire une application mobile, enrichir leur site... S'ils ne comprennent pas comment fonctionne votre API, comment vont-ils faire?

Le dossier vue contient les vues minimum pour que ASP.NET soit capable de générer **automatiquement** de la documentation qui expliquera à vos utilisateurs comment utiliser votre API.

->![Exemple de génération de documentation](/media/galleries/304/768c89cc-921a-493e-9bb8-6b4d5dc52b7e.png.960x960_q85.png)<-


*[API]: Application Programming Interface

*[REST]: Representational State Transfer
