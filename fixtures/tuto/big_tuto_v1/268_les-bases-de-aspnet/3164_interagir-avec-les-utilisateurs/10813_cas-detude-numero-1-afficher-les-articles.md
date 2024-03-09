Ce premier cas d'étude vous permettra de mettre en oeuvre :

- la création d'un contrôleur qui nous retourne une liste d'article
- la création d'une vue avec un modèle fortement typé
- l'utilisation du layout

# S'organiser pour répondre au problème

Comme c'est notre premier cas d'étude, je vais vous faire un pas à pas détaillé de ce qu'il faut faire puis vous coderez vous même les choses nécessaires.

1. Dans le contrôleur Article, créez une méthode List `public ActionResult List()`
2. Remplir la liste en utilisant la classe ArticleJSONRepository.cs
3. Ajouter une vue que le contrôleur va retourner, entrez les paramètres décrits dans le tableau


->
+----------------+-------------------------------------------------------------+
|paramètres      |  valeur                                                     |
+================+=============================================================+
|Nom             | List                                                        |
+----------------+-------------------------------------------------------------+
|Modèle          | List                                                        |
+----------------+-------------------------------------------------------------+
|Classe de modèle| Article (votre classe de modèle)                            |
+----------------+-------------------------------------------------------------+
|Utiliser une    |Oui                                                          |
|page de         |                                                             |
|disposition     |                                                             |
+----------------+-------------------------------------------------------------+
Tableau: les paramètres à entrer
![Liste des paramètres](/media/galleries/304/ab5d290c-79b9-4c78-8cf1-930e5c25d402.png.960x960_q85.png)<-

Voici le code qui permet de récupérer le chemin de votre fichier qui se trouve dans le dossier App_Data
```csharp
string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "App_Data", "liste_article_tuto_full.json");
```

Bien sur vous rajouterez un lien dans votre menu qui va permettre d'afficher votre liste d'article.

# Correction

Comme vous l'avez remarqué, c'est rapide de créer une vue qui affiche nos articles.
Bien sur comme d'habitude, je vous invite à lancer votre application pour voir le résultat et le code source généré.

[[secret]]
| ```csharp
| using Blog.Models;
| using System;
| using System.Collections.Generic;
| using System.IO;
| using System.Linq;
| using System.Web;
| using System.Web.Mvc;
|
| namespace Blog.Controllers
| {
|     public class ArticleController : Controller
|     {
|        /// <summary>
|        /// Champ qui va permettre d'appeler des méthodes pour faire des actions sur notre fichier
|        /// </summary>
|         private readonly ArticleJSONRepository _repository;
|
|         /// <summary>
|         /// Constructeur par défaut, permet d'initialiser le chemin du fichier JSON
|         /// </summary>
|         public ArticleController()
|         {
|             string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "App_Data", "liste_article_tuto_full.json");
|             _repository = new ArticleJSONRepository(path);
|         }
|
|         // GET: List
|         public ActionResult List()
|         {
|             try
|             {
|                 List<Article> liste = _repository.GetAllListArticle().ToList();
|                 return View(liste);
|             }
|             catch
|             {
|                 return View(new List<Article>());
|             }
|         }
|     }
| }
| ```
| Code: Le contrôleur
|
| ```csharp
| @model IEnumerable<Blog.Models.Article>
|
| @{
|     ViewBag.Title = "Blog";
| }
|
| <p>
|     @Html.ActionLink("Create New", "Create")
| </p>
| <table class="table">
|     <tr>
|         <th>
|             @Html.DisplayNameFor(model => model.Pseudo)
|         </th>
|         <th>
|             @Html.DisplayNameFor(model => model.Titre)
|         </th>
|         <th>
|             @Html.DisplayNameFor(model => model.Contenu)
|         </th>
|         <th></th>
|     </tr>
|
| @foreach (var item in Model) {
|     <tr>
|         <td>
|             @Html.DisplayFor(modelItem => item.Pseudo)
|         </td>
|         <td>
|             @Html.DisplayFor(modelItem => item.Titre)
|         </td>
|         <td>
|             @Html.DisplayFor(modelItem => item.Contenu)
|         </td>
|         <td>
|             @Html.ActionLink("Edit", "Edit", new { /* id=item.PrimaryKey */ }) |
|             @Html.ActionLink("Details", "Details", new { /* id=item.PrimaryKey */ }) |
|             @Html.ActionLink("Delete", "Delete", new { /* id=item.PrimaryKey */ })
|         </td>
|     </tr>
| }
|
| </table>
| ```
| Code: La vue

Jetons un coup d’œil à ce que nous a généré la vue :

- Un tableau qui affiche les propriétés publique de notre modèle Article;
- Différents liens qui pointent sur des méthodes du contrôleur : `Create` / `Edit` / `Details` / `Delete`.
