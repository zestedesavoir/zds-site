A plusieurs étapes du rendu, vous pouvez vous rendre compte que des filtres sont placés : ils sont faciles à reconnaître, car ils sont placé au dessus des méthodes, commençant par '[' et finissant par ']'. Un exemple que nous avons déjà vu :

```csharp
[HttpPost]
```

Ces filtres ont pour but d'automatiser certains traitements et en cas d'échec de ces derniers, ils redirigent l'utilisateur vers une page d'erreur.

Les filtres sont des attributs qui héritent de `FilterAttribute`. Comme ce sont des attributs, pour spécifier un filtre, il faut le placer au-dessus du nom de la méthode ou de la classe.

Lorsque vous spécifiez un filtre sur la classe, il s'appliquera à toutes les méthodes.

La plupart du temps, vous utiliserez les filtres [RequireRole], [Authorize], [AllowAnonymous].

Ces filtres ont la particularité de gérer les cas d'autorisation. Si Authorize ou RequireRole échouent, ils vous envoient une page avec pour erreur "403: not authorized".

Il est **fortement conseillé** de mettre `[Authorize]` sur **toutes les classes** de contrôleur puis de spécifier les méthodes qui sont accessibles publiquement à l'aide de `[AllowAnonymous]`.

Prenons l'exemple de notre blog, créons un contrôleur dont le but est de gérer les articles.

Une bonne pratique pour bien sécuriser votre blog sera :

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Mvc;

namespace mvc_vide.Controllers
{
    [Authorize]
    public class ArticleController : Controller
    {

        // GET: Article
        [AllowAnonymous]
        public ActionResult Index()
        {
            return View();
        }

        // GET: Article/Details/5
        [AllowAnonymous]
        public ActionResult Details(int id)
        {
            return View();
        }

        // GET: Article/Create
        public ActionResult Create()
        {
            return View();
        }

        // POST: Article/Create
        [HttpPost]
        public ActionResult Create(FormCollection collection)
        {
            try
            {
                // TODO: Add insert logic here

                return RedirectToAction("Index");
            }
            catch
            {
                return View();
            }
        }

        // GET: Article/Edit/5
        public ActionResult Edit(int id)
        {
            return View();
        }

        // POST: Article/Edit/5
        [HttpPost]
        public ActionResult Edit(int id, FormCollection collection)
        {
            try
            {
                // TODO: Add update logic here

                return RedirectToAction("Index");
            }
            catch
            {
                return View();
            }
        }

        // GET: Article/Delete/5
        public ActionResult Delete(int id)
        {
            return View();
        }

        // POST: Article/Delete/5
        [HttpPost]
        public ActionResult Delete(int id, FormCollection collection)
        {
            try
            {
                // TODO: Add delete logic here

                return RedirectToAction("Index");
            }
            catch
            {
                return View();
            }
        }
    }
}
```
Code: Restreindre l'accès par défaut

Vous pouvez, bien entendu ajouter plusieurs filtres à une même méthode. Dès lors, il est fortement conseillé de spécifier l'ordre d'exécution afin que tout soit prévisible.

Pour faire cela, il suffit de donner un paramètre nommé au filtre. Si vous désirez que l'autorisation soit exécutée en premier, faites : `[Authorize(Order:1)]`.
