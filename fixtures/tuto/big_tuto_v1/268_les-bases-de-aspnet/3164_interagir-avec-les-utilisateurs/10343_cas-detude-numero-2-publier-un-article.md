# Les étapes de la publication

Dans ce cas d'étude, nous ne parleront pas des autorisations, nous les mettrons en place **plus tard**, en partie III et IV.

Pour autant, il faut bien comprendre que la publication d'un article ne se fait pas au petit bonheur. Il va falloir respecter certaines étapes qui sont **nécessaires**.

Comme pour tout ajout de fonctionnalité à notre site, nous allons devoir créer une action. Par *convention* (ce n'est pas une obligation, mais c'est tellement mieux si vous respectez ça), l'action de **créer** du contenu s'appelle `Create`, celle d'éditer `Edit`, celle d'afficher le contenu seul (pas sous forme de liste)`Details`.

Le seul problème, c'est que la création se déroule en deux étapes :

- afficher le formulaire
- traiter le formulaire et enregistrer l'article ainsi posté.

Il va donc bel et bien falloir créer deux actions. Pour cela, nous allons utiliser la capacité de C# à nommer de la même manière deux méthodes différentes du moment qu'elles n'ont pas les mêmes arguments.

La méthode pour afficher le formulaire s'appellera `public ActionResult Create()`

Lorsque vous allez envoyer vos données, ASP.NET est capable de construire seul l'objet Article à partir de ce qui a été envoyé.
De ce fait, vous allez pouvoir appeler la méthode qui traitera le formulaire `public ActionResult Create(Article article)`. Elle devra comporter deux annotations qui seront détaillées ci-dessous :

```csharp
[HttpPost]
[ValidateAntiForgeryToken]
public ActionResult Create(Article article)
{
   //Votre code
}
```
Code: Protection contre la faille CSRF

C'est pour cela que de base, lorsque vous créerez la vue `Create.cshtml`, vous allez choisir comme modèle `Article` et comme template `Create`.
Ce template génère un formulaire complet qui possède deux capacités :

- envoyer un article quand vous le remplissez ;
- afficher les erreurs si jamais l'utilisateur a envoyé des données incomplètes ou mal formées.

Maintenant que vous avez vos deux actions et votre formulaire, nous allons pouvoir ajouter de la logique à notre application.

Principalement, cette logique sera toujours la même :

->![Logique pour la création de contenu](/media/galleries/304/8af676b8-45da-4728-bf20-3805e6988d4d.png.960x960_q85.jpg)<-

Le jeu sera donc de savoir :

- comment on valide
- comment on fait une redirection.

Je vous conseille de lancer l'application pour voir le rendu du formulaire.

Faites un clic-droit sur "*afficher le code source de la page*", je vous conseille de comparer le code HTML généré avec votre code `create.cshtml` pour voir le rendu des différents éléments de la page.


Il y a trois *helpers* à retenir (et uniquement trois !!) :

- `Html.LabelFor(model=>model.Propriete)` pour le label (exemple `Html.LabelFor(model => model.Titre)`)
- `Html.EditorFor(model=>model.Propriete)` pour le champ (exemple `Html.EditorFor(model => model.Titre)`)
- `Html.ValidationMessageFor(model=>model.Propriete)` pour le message d'erreur(exemple `Html.ValidationMessageFor(model => model.Titre)`)

[[i]]
| A noter, vous pourrez aussi trouver, au début du formulaire, `Html.ValidationSummary()` qui sert pour la sécurité.

Comme pour le formulaire, vous pouvez *customiser* le résultat de chacun des trois *helpers* en utilisant une version de la fonction qui a un argument appelé **htmlattributes**.

```csharp
@Html.LabelFor(model => model.Titre, htmlAttributes: new { @class = "control-label col-md-2" })
```
Code: Avec htmlattributes

En fin de tuto, vous pouvez retrouver un glossaire qui montre les différents contrôles razor et leur résultat en HTML.

Mais avant d'aller plus loin, un petit point sur les formulaires s'impose.

# Explication formulaire

Le formulaire est la façon la plus basique d'interagir avec l'utilisateur.
Derrière le mot "interagir", se cachent en fait deux actions : l'utilisateur vous demande des choses ou bien l'utilisateur vous envoie du contenu ou en supprime.

Ces actions sont distinguées en deux verbes :

- GET : l'utilisateur veut juste **afficher** le contenu qui existe *déjà*. Il est important de comprendre qu'une requête qui dit "GET" ne doit **pas** modifier d'informations dans votre base de données (sauf si vous enregistrez des statistiques)
- POST : l'utilisateur **agit** sur les données ou en *crée*. Vous entendrez peut être parler des verbes `PUT` et `DELETE`. Ces derniers ne vous seront utiles que si vous utilisez le JavaScript[^js_ajax] ou bien que vous développez une API REST. En navigation basique, seul `POST` est supporté.

[[a]]
| Vous avez sûrement remarqué : je n'ai pas encore parlé de sécurité. La raison est simple, `GET` ou `POST` n'apportent **aucune** différence du point de vue sécurité.
| Si quelqu'un vous dit le contraire, c'est qu'il a sûrement mal sécurisé son site.

Pour rappel un formulaire en HTML ressemble à ceci :

```html
<!-- permet de créer un formulaire qui ouvrira la page zestedesavoir.com/rechercher
l'attribut method="get", permet de dire qu'on va "lister" des choses
-->
<form id="search_form" class="clearfix search-form" action="/rechercher" method="get">
    <!-- permet de créer un champ texte, ici prérempli avec "zep".-->
    <input id="id_q" type="search" value="zep" name="q"></input>
    <button type="submit"></button><!-- permet de valider le formulaire-->

</form>
```
Code: un formulaire de recherche sur ZDS[^liste_type_input]

En syntaxe Razor, la balise `<form>` donne `HTML.BeginForm`, il existe différents paramètres pour définir si on est en "mode" GET ou POST, quel contrôleur appeler etc..
Bien sûr on peut très bien écrire le formulaire en HTML comme ci-dessus.

# Particularités d'un formulaire GET

Comme vous devez lister le contenu, le formulaire GET possède quelques propriétés qui peuvent s'avérer intéressantes.

- Toutes les valeurs se retrouvent placées à la fin de l'URL sous la forme :
`url_de_base/?nom_champ_1=valeur1&nom_champ2=valeur2`;
- L'url complète (url de base + les valeurs) ne doit pas contenir plus de 255 caractères;
- Si vous copiez/collez l'url complète dans un autre onglet ou un autre navigateur : vous aurez accès au **même résultat** (sauf si la page demande à ce que vous soyez enregistré!)[^indempotence].

# Particularités d'un formulaire POST

Les formulaires POST sont fait pour envoyer des contenus nouveaux. Ils sont donc beaucoup moins limités.

- il n'y a pas de limite de nombre de caractères;
- il n'y a pas de limite de caractères spéciaux (vous pouvez mettre des accents, des smiles...);
- il est possible d'envoyer un ou plusieurs fichiers, seul le serveur limitera la taille du fichier envoyé.

Comme pour les formulaires `GET`, les données sont entrées sous la forme de clef=>valeur. A ceci près que les formulaires `POST` envoient les données dans la requête HTTP elle-même et donc sont invisibles pour l'utilisateur lambda.
Autre propriété intéressante : si vous utilisez HTTPS, les données envoyées par POST sont cryptées. C'est pour ça qu'il est fortement conseillé d'utiliser ce protocole (quand on a un certificat[^ssl]) dès que vous demandez un mot de passe à votre utilisateur.


## Validation du formulaire

Les formulaires razor sont très intelligents et vous permettent d'afficher rapidement :

- le champ adapté à la donnée, par exemple si vous avez une adresse mail, il vous enverra un <input type="email"/>;
- l'étiquette de la donnée (la balise label) avec le bon formatage et le bon texte;
- les erreurs qui ont été détectées lors de l'envoi grâce à javascript (attention, c'est un confort, pas une sécurité);
- les erreurs qui ont été détectées par le serveur (là, c'est une sécurité).

Pour que razor soit capable de définir le bon type de champ à montrer, il faut que vous lui donniez cette indication dans votre classe de modèle. Cela permet aussi d'indiquer ce que c'est qu'un article *valide*.

Voici quelques attributs que l'on rencontre très souvent :

+-----------------------------------+----------------------------------+---------------------------------+
| Nom de l'attribut                 | Effet                            | Exemple                         |
+===================================+==================================+=================================+
| System.ComponentModel             | Force la propriété à être        | `[Required                      |
| .DataAnnotations.RequiredAttribute| toujours présente                | (AllowEmptyStrings=false)]`     |
+-----------------------------------+----------------------------------+---------------------------------+
|System.ComponentModel              | Permet de limiter la longueur    |`[StringLength(128)]`            |
|.DataAnnotations                   | d'un texte                       |                                 |
|.StringLengthAttribute             |                                  |                                 |
+-----------------------------------+----------------------------------+---------------------------------+
|System.ComponentModel              |Permet de limiter un nombre à un  |`[Range(128,156)]`               |
|.DataAnnotations.RangeAttriute     | intervalle donné                 |                                 |
+-----------------------------------+----------------------------------+---------------------------------+
|System.ComponentModel              |Permet d'indiquer que la chaîne de|`[Phone]`                        |
|.PhoneAnnotations                  |caractères est un numéro de       |                                 |
|                                   |téléphone                         |                                 |
+-----------------------------------+----------------------------------+---------------------------------+
Table: Les attributs communs

Il en existe beaucoup d'autres, pour gérer les dates, les expressions régulières... Vous pouvez vous même en créer si cela vous est nécessaire.

Avec ces attributs, décrivons notre classe Article. Par exemple de cette manière :

[[secret]]
| ```csharp
| using System;
| using System.Collections.Generic;
| using System.ComponentModel.DataAnnotations;
| using System.Linq;
| using System.Web;
|
| namespace Blog.Models
| {
|     /// <summary>
|     /// Notre modèle de base pour représenter un article
|     /// </summary>
|     public class Article
|     {
|         /// <summary>
|         /// Le pseudo de l'auteur
|         /// </summary>
|         [Required(AllowEmptyStrings=false)]
|         [StringLength(128)]
|         [RegularExpression(@"^[^,\.\^]+$")]
|         [DataType(DataType.Text)]
|         public string Pseudo { get; set; }
|         /// <summary>
|         /// Le titre de l'article
|         /// </summary>
|         [Required(AllowEmptyStrings = false)]
|         [StringLength(128)]
|         [DataType(DataType.Text)]
|         public string Titre { get; set; }
|         /// <summary>
|         /// Le contenu de l'article
|         /// </summary>
|         [Required(AllowEmptyStrings=false)]
|         [DataType(DataType.MultilineText)]
|         public string Contenu { get; set; }
|     }
| }
| ```
|

Maintenant, au sein de la méthode `Create(Article article)`, nous allons demander de valider les données.

Pour cela, il faut utiliser `ModelState.IsValid`.
```csharp
           if (ModelState.IsValid)
            {
                _repository.AddArticle(article);
                return RedirectToAction("List", "Article"); // Voir explication dessous
            }
            return View(article);
```
Code: validation des données et enregistrement

## Redirections

Comme nous l'avons vu dans le diagramme de flux, nous allons devoir rediriger l'utilisateur vers la page adéquate dans deux cas :

- Erreur fatale ;
- Réussite de l'action.

Dans le premier cas, il faut se rendre compte que, de base, ASP.NET MVC, enregistre des "filtres d'exception" qui, lorsqu'une erreur se passe, vont afficher une page "customisée".
Le comportement de ce filtre est celui-ci :

- Si l'exception attrapée hérite de `HttpException`, le moteur va essayer de trouver une page "personnalisée" correspondant au code d'erreur.
- Sinon, il traite l'exception comme une erreur 500.

Pour "customiser" la page d'erreur 500, il faudra attendre un peu, ce n'est pas nécessaire maintenant, au contraire, les informations de débogage que vous apportent la page par défaut sont très intéressantes.

Ce qui va nous intéresser, c'est plutôt la redirection "quand tout va bien".

Il existe deux méthodes pour rediriger selon vos besoin. La plupart du temps, vous utiliserez `RedirectToAction`. Cette méthode retourne un objet `ActionResult`.

Pour une question de lisibilité, je vous propose d'utiliser `RedirectToAction` avec deux (ou trois selon les besoins) arguments :

```csharp
RedirectToAction("NomDeL'action", "Nom du Contrôleur");//une redirection simple
```
```csharp
RedirectToAction("List","Article",new {page= 0});///Une redirection avec des paramètres pour l'URL
```

#Le code final

A chaque partie le code final est donnée, il ne faut pas copier bêtement. Pour bien comprendre les choses il faut regarder pas à pas les différentes actions, mettre des points d’arrêt dans les contrôleurs et regarder les différents objet.

![Mon point d’arrêt](http://i.imgur.com/4YlKRnX.png)

## l'entité Article
[[secret]]
|
| ```csharp
| public class Article
|     {
|         /// <summary>
|         /// Le pseudo de l'auteur
|         /// </summary>
|         [Required(AllowEmptyStrings=false)]
|         [StringLength(128)]
|         [RegularExpression(@"^[^,\.\^]+$")]
|         [DataType(DataType.Text)]
|         public string Pseudo { get; set; }
|         /// <summary>
|         /// Le titre de l'article
|         /// </summary>
|         [Required(AllowEmptyStrings = false)]
|         [StringLength(128)]
|         [DataType(DataType.Text)]
|         public string Titre { get; set; }
|         /// <summary>
|         /// Le contenu de l'article
|         /// </summary>
|         [Required(AllowEmptyStrings=false)]
|         [DataType(DataType.MultilineText)]
|         public string Contenu { get; set; }
|     }
| ```

## la vue Create

[[secret]]
| ```html
| @model Blog.Models.Article
|
| @{
|     ViewBag.Title = "Create";
| }
|
| <h2>Create</h2>
|
|
| @using (Html.BeginForm())
| {
|     @Html.AntiForgeryToken()
|
|     <div class="form-horizontal">
|         <h4>Article</h4>
|         <hr />
|         @Html.ValidationSummary(true, "", new { @class = "text-danger" })
|         <div class="form-group">
|             @Html.LabelFor(model => model.Pseudo, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Pseudo, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Pseudo, "", new { @class = "text-danger" })
|             </div>
|         </div>
|
|         <div class="form-group">
|             @Html.LabelFor(model => model.Titre, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Titre, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Titre, "", new { @class = "text-danger" })
|             </div>
|         </div>
|
|         <div class="form-group">
|             @Html.LabelFor(model => model.Contenu, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.TextAreaFor(model => model.Contenu, new { htmlAttributes = new { @class = "form-control" }, cols = 35, rows = 10 })
|                 @Html.ValidationMessageFor(model => model.Contenu, "", new { @class = "text-danger" })
|             </div>
|         </div>
|
|         <div class="form-group">
|             <div class="col-md-offset-2 col-md-10">
|                 <input type="submit" value="Create" class="btn btn-default" />
|             </div>
|         </div>
|     </div>
| }
|
| <div>
|     @Html.ActionLink("Back to List", "List")
| </div>
|
| <script src="~/Scripts/jquery-1.10.2.min.js"></script>
| <script src="~/Scripts/jquery.validate.min.js"></script>
| <script src="~/Scripts/jquery.validate.unobtrusive.min.js"></script>
|
| ```

## le contrôleur
[[secret]]
| ```csharp
|         //GET : Create
|         public ActionResult Create()
|         {
|             return View();
|         }
|
|         //POST : Create
|         [HttpPost]
|         [ValidateAntiForgeryToken]
|         public ActionResult Create(Article article)
|         {
|             if (ModelState.IsValid)
|             {
|                 _repository.AddArticle(article);
|                 return RedirectToAction("List", "Article");
|             }
|             return View(article);
|         }
| ```

[^js_ajax]: une technique avancée mais néanmoins courante dans le web moderne est l'utilisation de JavaScript avec l'objet XMLHttpRequest. L’acronyme qui désigne cette utilisation est *AJAX*.
[^liste_type_input]: la liste complète des types de champ HTML se trouve [ici](http://www.alsacreations.com/tuto/lire/1372-formulaires-html5-nouveaux-types-champs-input.html).
[^indempotence]: On parle d'[indempotence](http://fr.wikipedia.org/wiki/Idempotence#En_informatique).
[^ssl]: le protocole HTTPS garantie la confidentialité (i.e ce qui est transmis est secret) et l'authenticité (i.e que le site est bien qui il prétend être) et pour cela il faut acheter un [certificat](http://fr.wikipedia.org/wiki/Certificat_%C3%A9lectronique).
