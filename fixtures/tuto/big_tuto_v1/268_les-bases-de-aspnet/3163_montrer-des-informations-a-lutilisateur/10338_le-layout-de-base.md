Nous allons maintenant créer notre premier **layout** avec Razor.

[[question]]
| C'est quoi un layout ?

Layout est un mot anglais signifiant **mise en page**. Supposez que vous développez votre propre application avec ASP.NET et que vous souhaitez conserver un style cohérent pour chaque page de votre application. Prenons quelques pages de Zeste de Savoir :

![Page d'accueil](/media/galleries/304/7836ad6b-6531-4528-b61b-a8ac55d65472.png.960x960_q85.jpg)

![Page des tutoriels](/media/galleries/304/90c0a3ec-bfcb-418c-abed-e2289b792b24.png.960x960_q85.jpg)

![Pages des articles](/media/galleries/304/507e6b0a-887e-4b44-b108-992ce90d5baa.png.960x960_q85.jpg)

Nous remarquons qu'à chaque page, il existe une mise en page semblable : l'en-tête, le pied de page et la barre de navigation. Tout ce qui change est le **contenu** (qui se situe au centre). Il y a deux solutions pour faire cela :

- réécrire le code de l'en-tête, de la barre de navigation et du pied de page sur toutes les pages.
- définir un modèle commun pour l'application avec lequel chaque page pourra ou non l'utiliser.

La deuxième solution semble la meilleure et la moins fatigante. C'est justement le principe d'un layout. D'ailleurs, souvenez-vous de nos premières vues, en haut du fichier **cshtml** il y avait un bloc Razor :

```html
@{
    Layout = null;
}
```

C'est cette ligne qui indique si un layout est ou non utilisé. Place à la pratique ! nous allons créer notre premier layout. Pour cela, dans notre projet Blog, ajoutez un dossier **Content**. Ce dossier va contenir les fichiers de styles (CSS). Ensuite, dans ce dossier Content, ajoutez un fichier CSS que nous nommerons **Blog.css**.

Ensuite, ajoutez un dossier **Shared** dans le dossier Views. Par convention, en ASP.NET, le dossier Shared situé dans Views contient tous les layouts pour votre application. Il est destiné à contenir les éléments partagés entre les différentes vues.

Pour terminer, ajoutez un fichier **_Layout.cshtml** dans le dossier Shared de notre Blog. Ce fichier _Layout.cshtml va représenter notre fichier de mise en page.

![Ajouter une page de disposition( layout)](/media/galleries/304/f47cea5f-0796-417e-9876-23aeda5be601.png.960x960_q85.jpg)

Notre solution doit ressembler à ceci maintenant :

![Solutions après ajout des dossiers et des fichiers](/media/galleries/304/fa218802-dcb5-48be-83f5-b76c1b3b504f.png.960x960_q85.jpg)

Notre fichier _Layout.cshtml contient déjà un peu de code :

```html
<!DOCTYPE html>

<html>
<head>
    <meta name="viewport" content="width=device-width" />
    <title>@ViewBag.Title</title>
</head>
<body>
    <div>
        @RenderBody()
    </div>
</body>
</html>
```

Deux éléments vont porter notre attention : ```@ViewBag.Title``` et ```@RenderBody```. Une page de disposition n'est pas un fichier HTML comme un autre, outre le fait qu'il contient du code Razor, cette page ne sera jamais affichée directement à l'utilisateur ! Ce sont les vues qui vont l'utiliser et pas l'inverse. Lorsque nous créerons une vue qui utilisera notre layout, cette dernière va transmettre des information au layout : le titre de la page de vue (```@ViewBag.Title```) et le contenu de la vue (```@RenderBody```).

Cette présentation est un peu vide, nous allons la garnir un petit peu :

```html
<!DOCTYPE html>

<html>
<head>
    <meta name="viewport" content="width=device-width" />
    <title>@ViewBag.Title - Blog</title>
    <link rel="stylesheet" href="@Url.Content("~/Content/Blog.css")" type="text/css" />
</head>
<body>
    <header>
        <h1>Mon Blog ASP.NET MVC</h1>
        <ul id="navliste">
            <li class="premier"><a href="/Accueil/" id="courant">Accueil</a></li>
            <li><a href="/Accueil/About/">A Propos</a></li>
        </ul>
    </header>
    <div id="corps">
        @RenderBody()
    </div>
    <footer>
        <p>@DateTime.Now.Year - Mon Blog MVC</p>
    </footer>
</body>
</html>
```

Voici le contenu du fichier **Blog.css** :

[[secret]]
| ```css
| * {
|     margin: 0px;
|     padding: 0px;
|     border: none;
| }
|
| body {
|     font-family: Arial, Helvetica, sans-serif;
|     font-size: 14px;
|     background-color: #FBF9EF;
|     padding: 0px 6%;
| }
|
| header {
|     float: left;
|     width: 100%;
|     border-bottom: 1px dotted #5D5A53;
|     margin-bottom: 10px;
| }
|
| header h1 {
|     font-size: 18px;
| 	float: left;
|     padding: 45px 0px 5px 0px;
| }
|
| ul li a {
|     font-size: 16px;
| }
|
| ul
| {
| 	list-style-type: square;
| 	margin-left: 25px;
| 	font-size: 14px;
| }
|
| footer {
|     width: 100%;
|     border-top: 1px dotted #5D5A53;
|     margin-top: 10px;
|     padding-top: 10px;
| }
|
| /* barre de navigation header */
|
| ul#navliste
| {
| 	float: right;
| }
|
| ul#navliste li
| {
| 	display: inline;
| }
|
| ul#navliste li a
| {
| 	border-left: 1px dotted #8A8575;
| 	padding: 10px;
| 	margin-top: 10px;
| 	color: #8A8575;
| 	text-decoration: none;
| 	float: left;
| }
|
| ul#navliste li:first-child a
| {
| 	border: none;
| }
|
| ul#navliste li a:hover
| {
| 	color: #F6855E;
| }
|
| /* fin barre de navigation header*/
|
| p
| {
| 	margin-bottom: 15px;
| 	margin-top: 0px;
| }
|
| h2
| {
| 	color: #5e5b54;
| }
|
| header h1 a
| {
| 	color: #5E5B54;
| }
|
| a:link, a:visited
| {
| 	color: #F6855E;
| 	text-decoration: none;
| 	font-weight: bold;
| }
|
| a:hover
| {
| 	color: #333333;
| 	text-decoration: none;
| 	font-weight: bold;
| }
|
| a:active
| {
| 	color: #006633;
| 	text-decoration: none;
| 	font-weight: bold;
| }
| ```

Nous avons notre page de layout. Maintenant, il faudrait placer une vue (par exemple celle de la page d'accueil) pour admirer le résultat. C'est-ce que nous allons faire !

Pour qu'une page de vue utilise un layout, il y a deux solutions : soit placer le nom du layout comme valeur de la variable Layout en haut de la vue, soit ajouter une page de vue qui va automatiquement ajouter le layout à chaque vue de notre application (cela signifie que nous n'aurons pas besoin d'indiquer le layout à chaque page).

Comme nous sommes fainéant et qu'ajouter ```Layout = "/Views/Shared/_Layout.cshtml"``` à chaque page est trop répétitif, nous allons utiliser la deuxième solution. Nous allons donc créer un fichier **_ViewStart**. Faites un clic droit sur le répertoire Views > Ajouter > **Nouvel élément**.

![Ajout du fichier _ViewStart](/media/galleries/304/9bab9f7a-19b6-4c82-a770-5182d5f1e8e7.png.960x960_q85.jpg)

Sélectionnez Page de vue MVC avec disposition et nommez-là **_ViewStart.cshtml**. Ce fichier va simplement contenir :

```html
@{
    Layout = "~/Views/Shared/_Layout.cshtml";
}
```

[[information]]
| Ce fichier de disposition doit se nommer _ViewStart. C'est une convention.

### Ajout du contrôleur

Ajoutons le contrôleur de notre page d'accueil. Ce contrôleur  va contenir deux méthodes : **Index** et **About** (chacune désignant une page de l'application). C'est pour cela que nous vous avons fait placer les URLs suivantes dans la barre de navigation :

```html
<li class="premier"><a href="/Accueil/" id="courant">Accueil</a></li>
<li><a href="/Accueil/About/">A Propos</a></li>
```

Nous appellerons le contrôleur **AccueilController**.

```csharp
namespace BlogMVC.Controllers
{
    public class AccueilController : Controller
    {
        //
        // GET: /Accueil/
        public ActionResult Index()
        {
            return View();
        }

        //
        // GET: /About/
        public ActionResult About()
        {
            return View();
        }
    }
}
```

Les méthodes ne contiennent, pour l'instant, rien de spécial. Ensuite, nous allons ajouter la vue correspondant à l'index. Faites clic-droit sur la méthode Index >** Ajouter une vue**...

![Ajout de la vue Index du blog](/media/galleries/304/fde08fb6-5a40-439f-83a1-b07691e0f3bc.png.960x960_q85.jpg)

Prenez soin de cocher la case "Utiliser une page de disposition". L'avantage de notre fichier ViewStart, c'est que nous n'avons pas besoin d'indiquer le layout. La vue Index est généré :

```html
@{
    ViewBag.Title = "Index";
}

<h2>Index</h2>
```

Ce sera suffisant. Testons notre application :

![Tester notre layout](/media/galleries/304/6f3f4339-a45e-47be-bba2-b5b93e9baf9e.png.960x960_q85.jpg)

![Page d'accueil](/media/galleries/304/c40a1bd3-e92c-4367-91e6-9e6fb6315513.png.960x960_q85.jpg)

Il suffit de recommencer la même opération sur la méthode ```About``` pour générer la vue /About/. Toutes nos vues auront désormais la même mise en page sans que nous ayons à répéter les mêmes choses à chaque fois.

![Solution initiale de notre Blog](/media/galleries/304/6beb61ec-3d76-43ab-8f9c-6a395166ff7a.png.960x960_q85.jpg)
