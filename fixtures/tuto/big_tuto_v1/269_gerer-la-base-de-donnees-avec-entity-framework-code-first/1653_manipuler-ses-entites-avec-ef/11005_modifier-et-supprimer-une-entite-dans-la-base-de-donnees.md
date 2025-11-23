# Préparation

Ici le cas sera plus "complexe" si je puis dire. En effet, pour s'assurer que quoi qu'il arrive le changement soit bien détecté sans perte de performance (c'est à dire qu'on ne va pas demander au système de comparer caractère par caractère le texte de l'article pour détecter le changement), il faudra forcer un peu les choses.

1. Premièrement, il faudra aller chercher l'objet tel qu'il est stocké en base de données.
1. Ensuite il faudra annoncer à EntityFramework "je vais le modifier".
1. Enfin il faudra mettre en place les nouvelles valeurs.

Tout cela devra être mis dans la méthode "Edit" de votre contrôleur.

```csharp
        [HttpGet]
        public ActionResult Edit(int id)
        {
            return View();
        }
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Edit(int id, ArticleCreation articleCreation)
        {
            return RedirectToAction("List");
        }
```
Code: Les méthodes d'édition

[[i]]
|Toutes les étapes sont importantes. Si vous ne faites pas la première, EF va possiblement croire que vous êtes en train de créer une **nouvelle** entité.

Je vous encourage à créer la vue Edit comme nous l'avions vu plus tôt. Il faudra aussi apporter quelques légères modifications à la vue `List` pour que la page d'édition soit accessible :

Trouvez les trois lignes suivantes
```
                    @Html.ActionLink("Edit", "Edit", new { /* id=item.PrimaryKey */ }) |
                    @Html.ActionLink("Details", "Details", new { /* id=item.PrimaryKey */ }) |
                    @Html.ActionLink("Delete", "Delete", new { /* id=item.PrimaryKey */ })
```
Code: Les liens incomplets

Et mettez-y l'ID de l'article :

```csharp
                    @Html.ActionLink("Edit", "Edit", new {  id=item.ID  }) |
                    @Html.ActionLink("Details", "Details", new { /* id=item.PrimaryKey */ }) |
                    @Html.ActionLink("Delete", "Delete", new {  id=item.ID })
```
Code: Les liens sont corrects.

# Modifier l'entité

Pour trouver l'entité, vous pouvez utiliser la méthode `Where` comme vue précédemment. Le problème de cette méthode, c'est qu'elle retourne une collection, même si cette dernière ne contient qu'un élément.

Il vous faudra dès lors utiliser la méthode `FirstOrDefault` pour aller chercher l'entité.

Une alternative sera d'utiliser la méthode `Find`, c'est ce que nous ferons dans cette partie.

Une fois l'entité trouvée, il faut annoncer au contexte qu'elle est modifiée. C'est là que commence la partie "complexe" puisque pour s'assurer que la modification soit efficace et effective dans tous les cas, nous allons utiliser une capacité avancée de EntityFramework.

Le contexte de données contient une méthode `Entry<TEntity>()` qui permet de personnaliser la manière dont les entités sont gérées par Entity Framework.

Cette méthode retourne un objet de type `DbEntityEntry` qui a la possibilité de forcer l'état d'une entité, utiliser des fonctionnalité de différentiel (c'est à dire trouver la différence entre l'ancienne et la nouvelle version)...

Pour vous aider, voici le code :

```csharp hlines="16-25"
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Edit(int id, ArticleCreation articleCreation)
        {
            Article entity = bdd.Articles.Find(id);
            if (entity == null)
            {
                return RedirectToAction("List");
            }
            string fileName;
            if (!handleImage(articleCreation, out fileName))
            {

                return View(articleCreation);
            }
            DbEntityEntry<Article> entry = bdd.Entry(entity);
            entry.State = System.Data.Entity.EntityState.Modified;
            Article article = new Article
            {
                Contenu = articleCreation.Contenu,
                Pseudo = articleCreation.Pseudo,
                Titre = articleCreation.Titre,
                ImageName = fileName
            };
            entry.CurrentValues.SetValues(article);
            bdd.SaveChanges();

            return RedirectToAction("List");
        }
```
Code: la méthode Edit

[[i]]
|J'ai encapsulé la gestion de l'image dans une méthode pour que ça soit plus facile à utiliser.

[[secret]]
| ```csharp
|         private bool handleImage(ArticleCreation articleCreation, out string fileName)
|         {
|             bool hasError = false;
|             fileName = "";
|             if (articleCreation.Image != null)
|             {
|
|                 if (articleCreation.Image.ContentLength > 1024 * 1024)
|                 {
|                     ModelState.AddModelError("Image", "Le fichier téléchargé est trop grand.");
|                     hasError = true;
|                 }
|
|                 if (!AcceptedTypes.Contains(articleCreation.Image.ContentType)
|                        || AcceptedExt.Contains(Path.GetExtension(articleCreation.Image.FileName).ToLower()))
|                 {
|                     ModelState.AddModelError("Image", "Le fichier doit être une image.");
|                     hasError = true;
|                 }
|
|                 try
|                 {
|                     string fileNameFile = Path.GetFileName(articleCreation.Image.FileName);
|                     fileName = new SlugHelper().GenerateSlug(fileNameFile);
|                     string imagePath = Path.Combine(Server.MapPath("~/Content/Upload"), fileName);
|                     articleCreation.Image.SaveAs(imagePath);
|                 }
|                 catch
|                 {
|                     fileName = "";
|                     ModelState.AddModelError("Image", "Erreur à l'enregistrement.");
|                     hasError = true;
|                 }
|
|             }
|             return !hasError;
|         }
| ```
| Code: gestion de l'image

# La suppression de l'entité

La suppression se veut, bien heureusement plus simple.

Si l'utilisation de `Entry` est toujours possible, avec un simple changement d'état à `Deleted`, vous pouvez utiliser la méthode `bdd.Articles.Remove` qui prend en paramètre votre entité.

N'oubliez pas de sauvegarder les changements et c'est bon.

Par contre, je tenais à préciser une chose : la vue par défaut vous propose d'utiliser un lien et donc une requête GET. Il vaut mieux changer ça !

Utilisez une requête `POST` et assurez-vous d'être protégés contre la faille csrf.

Je vous laisse le faire en exercice.

[[secret]]
| ```csharp
|         [HttpPost]
|         [ValidateAntiForgeryToken]
|         public ActionResult Delete(int id)
|         {
|             Article a = bdd.Articles.Find(id);
|             if (a == null)
|             {
|                 return RedirectToAction("List");
|             }
|             bdd.Articles.Remove(a);
|             bdd.SaveChanges();
|             return RedirectToAction("List");
|         }
| ```
| Code: le contrôleur de suppression
|
| ```html
| @using (Html.BeginForm("Delete", "Article", new { id = item.ID }, FormMethod.Post, null))
|                     {
|                         Html.AntiForgeryToken();
|                         <button type="submit">Supprimer</button>
|                     }
| ```
| Code: le code à changer dans la vue
