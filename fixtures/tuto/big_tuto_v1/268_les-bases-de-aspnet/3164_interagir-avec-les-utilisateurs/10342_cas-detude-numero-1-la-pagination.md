Ce premier cas d'étude vous permettra de mettre en oeuvre :

- la création d'une vue avec un modèle fortement typé
- l'utilisation d'un formulaire simple
- l'utilisation d'un layout

# Ce qu'est la pagination

La pagination, c'est une technique très utile quand vous devez afficher des listes très longues de contenu.
Sur un blog, vous aurez - à partir d'un moment - une liste assez importante d'articles. Disons pour faire simple que vous en avez 42.

Pensez-vous qu'afficher les 42 articles sur la page d'accueil soit une bonne chose?

42 articles, c'est long, c'est lourd. Cela ralentirait le chargement de votre page et ça forcerait vos utilisateur à utiliser l'ascenseur un trop grand nombre de fois.

De ce fait, vous allez décider de n'afficher que 5 articles et de mettre les 5 suivants dans une autre page et ainsi de suite.

Votre but sera donc d'afficher la liste des articles puis de mettre à disposition de vos utilisateurs un bouton "page précédente", un autre "page suivante", et un formulaire permettant de se rendre à une page quelconque.

Voici un petit aperçu du contrôle proposé :

-> ![Aperçu formulaire pagination](/media/galleries/304/5f1b9af0-3999-4039-9a9b-b8a61210c4db.png.960x960_q85.png) <-

# S'organiser pour répondre au problème

Comme c'est notre premier cas d'étude, vous vais vous faire un pas à pas détaillé de ce qu'il faut faire puis vous coderez vous même les choses nécessaires.

1. Dans le contrôleur Article, créez une méthode List `public ActionResult List(int page = 0)`
2. Rendez-vous dans le dossier `View\Article`, cliquez-droit, `Ajouter`->`Vue`, Entrez les paramètres décrits dans le tableau
3. Ajoutez les liens Précédent/Suivant à la vue
4. Déterminez si vous devez utiliser un formulaire GET ou POST et créez-le.

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
|Utiliser une    |oui : `~/Views/Shared/_Layout.cshtml`                        |
|page de         |                                                             |
|disposition     |                                                             |
+----------------+-------------------------------------------------------------+
Tableau: les paramètres à entrer
![Liste des paramètres](/media/galleries/304/ab5d290c-79b9-4c78-8cf1-930e5c25d402.png.960x960_q85.png)<-



# Correction

Comme vous l'aurez sûrement compris, nous sommes dans le cas d'un formulaire qui demande un affichage. Donc on va utiliser GET.


[[secret]]
|
| ```csharp
|         public ActionResult List(int page = 0)
|         {
|             //var path = ConfigurationManager.AppSettings["jsonlist"];
|             var path = @"D:\VSProj\TutoBlog\TutoBlog\App_Data\liste_article_tuto_full.json";
|             var repository = new ArticleJSONRepository(path);
|             ViewBag.Page = page;
|             try
|             {
|                 var liste = repository.GetList(page * ArticlePerPage, ArticlePerPage).ToList();
|                 return View(liste);
|             }
|             catch
|             {
|                 return View(new List<Article>());
|             }
|
|         }
| ```
| Code: Le contrôleur
|
| ```csharp
| @model List<TutoBlog.Models.Article>
|
| @{
|     ViewBag.Title = "Liste des articles";
|     Layout = "~/Views/Shared/_Layout.cshtml";
| }
| <section>
|     <h2>List</h2>
|
|     <p>
|         @Html.ActionLink("Create New", "Create")
|     </p>
|     <table class="table">
|         <tr>
|             <th>
|                 @Html.DisplayNameFor(model => model[0].Pseudo)
|             </th>
|             <th>
|                 @Html.DisplayNameFor(model => model[0].Titre)
|             </th>
|             <th>
|                 @Html.DisplayNameFor(model => model[0].Contenu)
|             </th>
|             <th></th>
|         </tr>
|
|         @foreach (var item in Model)
|         {
|             <tr>
|                 <td>
|                     @Html.DisplayFor(modelItem => item.Pseudo)
|                 </td>
|                 <td>
|                     @Html.DisplayFor(modelItem => item.Titre)
|                 </td>
|                 <td>
|                     @Html.DisplayFor(modelItem => item.Contenu)
|                 </td>
|                 <td>
|                     @Html.ActionLink("Edit", "Edit", new { /* id=item.PrimaryKey */ }) |
|                     @Html.ActionLink("Details", "Details", new { /* id=item.PrimaryKey */ }) |
|                     @Html.ActionLink("Delete", "Delete", new { /* id=item.PrimaryKey */ })
|                 </td>
|             </tr>
|         }
|
|     </table>
|     <footer class="pagination-nav">
|         <ul>
|             <li>
|                 @if ((int)ViewBag.Page > 0)
|                 {
|
|                     @Html.ActionLink("Précédent", "List", "Article", new { page = ViewBag.Page - 1 }, new { @class = "button" })
|
|                 }
|             </li>
|             <li>
|                 @if (Model.Count == TutoBlog.Controllers.ArticleController.ArticlePerPage || ViewBag.Page > 0)
|                 {
|                     using (Html.BeginForm("List", "Article", FormMethod.Get))
|                     {
|                         @Html.TextBox("page", 0, new { type = "number" })
|                         <button type="submit">Aller à</button>
|
|                     }
|
|
|                 }
|             </li>
|             <li>
|                 @if (Model.Count == TutoBlog.Controllers.ArticleController.ArticlePerPage)
|                 {
|                     @Html.ActionLink("Suivant", "List", "Article", new { page = ViewBag.Page + 1 }, new { @class = "button" })
|
|                 }
|             </li>
|         </ul>
|     </footer>
| </section>
| ```
| Code: La vue
|
