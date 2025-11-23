# Ce qu'est la pagination

La pagination, c'est une technique très utile quand vous devez afficher des listes très longues de contenu.
Sur un blog, vous aurez - à partir d'un moment - une liste assez importante d'articles. Disons pour faire simple que vous en avez 42.

Pensez-vous qu'afficher les 42 articles sur la page d'accueil soit une bonne chose?

42 articles, c'est long, c'est lourd. Cela ralentirait le chargement de votre page et ça forcerait vos visiteurs à utiliser l'ascenseur un trop grand nombre de fois.

De ce fait, vous allez décider de n'afficher que 5 articles et de mettre les 5 suivants dans une autre page et ainsi de suite.

Votre but sera donc d'afficher la liste des articles puis de mettre à disposition de vos utilisateurs un bouton "page précédente", un autre "page suivante", et un formulaire permettant de se rendre à une page quelconque.

Voici un petit aperçu du contrôle proposé :

-> ![Aperçu formulaire pagination](/media/galleries/304/5f1b9af0-3999-4039-9a9b-b8a61210c4db.png.960x960_q85.png) <-

# S'organiser pour répondre au problème

Comme c'est notre dernier cas d'étude pour ce chapitre, vous allez utiliser toutes votre connaissance apprise jusqu'ici.

1. Dans le contrôleur Article, modifier la méthode List en `public ActionResult List(int page = 0)`
2. Utilisez la bonne méthode pour récupérer vos articles, voir `ArticleJSONRepository`
3. Ajoutez les liens Précédent/Suivant dans la vue, `@Html.ActionLink()`
4. Déterminez si vous devez utiliser un formulaire GET ou POST et créez-le. (url de type url/Article/List?page=0)

[[secret]]
|
| ```csharp
|         public readonly static int ARTICLEPERPAGE = 5;
|
|         // GET: List
|         public ActionResult List(int page = 0)
|         {
|             try
|             {
|                 List<Article> liste = _repository.GetListArticle(page * ARTICLEPERPAGE, ARTICLEPERPAGE).ToList();
|                 ViewBag.Page = page;
|                 return View(liste);
|             }
|             catch
|             {
|                 return View(new List<Article>());
|             }
|         }
| ```
| Code : le contrôleur
|
| ```csharp
| @model IEnumerable<Blog.Models.Article>
|
| @{
|     ViewBag.Title = "Blog";
| }
|
| <section>
|     <p>
|         @Html.ActionLink("Create New", "Create")
|     </p>
|     <table class="table">
|         <tr>
|             <th>
|                 @Html.DisplayNameFor(model => model.Pseudo)
|             </th>
|             <th>
|                 @Html.DisplayNameFor(model => model.Titre)
|             </th>
|             <th>
|                 @Html.DisplayNameFor(model => model.Contenu)
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
|                     @{
|                        if (!string.IsNullOrWhiteSpace(item.ImageName))
|                        {
|                          <img src="~/Content/Upload/@item.ImageName" alt="@Path.GetFileNameWithoutExtension(item.ImageName)" />
|                        }
|                     }
|                 </td>
|                 <td>
|                     @Html.ActionLink("Edit", "Edit", new { /* id=item.PrimaryKey */ }) |
|                     @Html.ActionLink("Details", "Details", new { /* id=item.PrimaryKey */ }) |
|                     @Html.ActionLink("Delete", "Delete", new { /* id=item.PrimaryKey */ })
|                 </td>
|             </tr>
|         }
|     </table>
|
|     <footer class="pagination-nav">
|         <ul>
|             <li>
|                 @if ((int)ViewBag.Page > 0)
|                 {
|                     @Html.ActionLink("Précédent", "List", "Article", new { page = ViewBag.Page - 1 }, new { @class = "button" })
|                 }
|             </li>
|             <li>
|                 @if (Model.Count() == Blog.Controllers.ArticleController.ARTICLEPERPAGE || ViewBag.Page > 0)
|                 {
|                     using (Html.BeginForm("List", "Article", FormMethod.Get))
|                     {
|                         @Html.TextBox("page", 0, new { type = "number" })
|                         <button type="submit">Aller à</button>
|                     }
|                 }
|             </li>
|             <li>
|                 @if (Model.Count() == Blog.Controllers.ArticleController.ARTICLEPERPAGE)
|                 {
|                     @Html.ActionLink("Suivant", "List", "Article", new { page = ViewBag.Page + 1 }, new { @class = "button" })
|                 }
|             </li>
|         </ul>
|     </footer>
| </section>
| ```
| Code : la vue
