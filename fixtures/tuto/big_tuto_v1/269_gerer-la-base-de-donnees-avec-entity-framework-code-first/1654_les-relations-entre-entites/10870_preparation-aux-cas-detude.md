Comme pour la partie précédente, nous allons apprendre les différentes notions qui vont suivre *via* deux cas d'étude.

Qui dit "cas d'étude" dit "ajustement à opérer". L'avantage, contrairement aux cas d'études déjà réalisés, c'est que cette fois-ci, vous pouvez votre la préparation comme un TP en soit.

En effet, vous avez sûrement remarqué qu'ASP.NET aimerait que vous développiez une page `Article/Details`.
C'est ce que nous allons devoir faire dans un premier temps.

Comme cela peut être vu comme un TP, la "correction" sera masquée.

[[secret]]
| ```csharp
|         public ActionResult Details(int id)
|         {
|             Article art = bdd.Articles.Find(id);
|             if (art == null)
|             {
|                 return new HttpNotFoundResult();
|             }
|             return View(art);
|         }
| ```
| Code: L'action Details dans le contrôleur
|
| ```html
| @model Blog.Models.Article
| @using Blog.Models;
| <section>
|     <h1>@Html.DisplayFor(model => model.Titre)</h1>
|     <hr />
|     <header>
|         <dl class="dl-horizontal">
|             <dt>
|                 @Html.DisplayNameFor(model => model.Pseudo)
|             </dt>
|
|             <dd>
|                 @Html.DisplayFor(model => model.Pseudo)
|             </dd>
|             <dd>
|                 <img src="@Html.DisplayFor(model => model.ImageName)" alt="@Html.DisplayFor(m => m.Titre)" />
|             </dd>
|
|         </dl>
|     </header>
|     <article>
|         @Html.DisplayFor(model => model.Contenu)
|     </article>
| </section>
| <footer>
|     @Html.ActionLink("Edit", "Edit", new { id = Model.ID }) |
|     @Html.ActionLink("Retour à la liste", "List")
| </footer>
|
| ```
| Code: La vue Article/Details.cshtml
