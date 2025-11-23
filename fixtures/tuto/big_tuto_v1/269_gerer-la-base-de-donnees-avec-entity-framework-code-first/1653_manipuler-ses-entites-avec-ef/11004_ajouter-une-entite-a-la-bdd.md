# Quelques précisions

Avant de montrer le code qui vous permettra de sauvegarder vos entités dans la base de données, je voudrais vous montrer plus en détail comment Entity Framework gère les données.

![Fonctionnement de EntityFramework](/media/galleries/304/749c8cc0-a21d-4a5c-98bc-979f8888855b.png.960x960_q85.jpg)

Comme le montre le schéma, une entité n'est pas *tout de suite* envoyée à la base de données. En fait pour que cela soit fait il faut que vous demandiez à la base de données de **persister** tous les changements en attente.

[[i]]
|"détachés" est "supprimés" sont des états qui se ressemblent beaucoup. En fait "détaché" cela signifie que la suppression de l'entité a été persistée.

A partir de là, le système va chercher parmi vos entités celles qui sont marquées :

- créées;
- modifiées;
- supprimées.

Et il va mettre en place les actions adéquates.

La grande question sera donc :

[[q]]
|Comment marquer les entités comme "créées"?

# Ajouter une entité

C'est l'action la plus simple de toutes : `bdd.VotreDbSet.Add(votreEntite);` et c'est tout!

Ce qui transforme notre code d'envoie d'article en :

```csharp hl_lines="24-25"
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Create(ArticleCreation articleCreation)
        {
            if (!ModelState.IsValid)
            {
                return View(articleCreation);
            }

            string fileName = "";
            if (articleCreation.Image != null)
            {
                /* gestion de l'erreur pour l'image */
            }

            Article article = new Article
            {
                Contenu = articleCreation.Contenu,
                Pseudo = articleCreation.Pseudo,
                Titre = articleCreation.Titre,
                ImageName = fileName
            };

            bdd.Articles.Add(article);
            bdd.SaveChanges();

            return RedirectToAction("List", "Article");
        }
```
Code: Persistance de l'article en base de données
