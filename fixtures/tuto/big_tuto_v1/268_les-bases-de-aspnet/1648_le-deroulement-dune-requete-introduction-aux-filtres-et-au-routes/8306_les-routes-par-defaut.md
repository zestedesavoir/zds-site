les routes par défaut

```csharp
routes.MapRoute(
     name: "Default",
     url: "{controller}/{action}/{id}",
     defaults: new { controller = "Home", action = "Index", id = UrlParameter.Optional }
);
```
Comme il s'agit d'une route globale, on lui donne un nom : "Default".
La partie intéressante vient avec la partie "url". Il vous dit que par défaut une url doit être composée :

- du nom du contrôleur;
- du nom de l'action;
- d'un id

`{controller}` et `{action}` sont des mots clefs qui sont immédiatement reconnus par le routeur.

Par contre "id" est un paramètre qui est propre à notre application ([UrlParameter](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.urlparameter(v=vs.118).aspx)).
Dans la ligne qui suit, on vous informe qu'il est optionnel.

[[question]]
|Pourquoi ils ont mis "id" s'il est optionnel et puis il sert à quoi?

Souvenez-vous, je vous ai dit dès le départ que la grande force de MVC, c'est que c'était normalisé.
En fait vous faites cinq types d'actions le plus souvent :

- obtenir une liste
- créer un nouvel objet
- détailler un objet de la liste
- modifier cet objet
- supprimer un objet

Dans les deux premiers cas, vous avez juste besoin de donner le nom de l'action (lister ou créer). Par contre dans le second cas, vous avez besoin de retrouver un objet en particulier. Le plus souvent, pour cela, vous allez utiliser un **identifiant**. Pour aller plus vite, on écrit "id".
Prenons un exemple pour notre blog :
Nos visiteurs voudront avoir la liste de nos articles, puis pourquoi pas ne voir qu'un seul article en particulier.
Ce qui équivaudrait à `/articles/liste` et `/articles/detail/5` (pour le 5ème article).


Pour les auteurs d'article, nous avons la même chose du côté de l'édition : `/articles/creer` et `/articles/modifier/5`.

Dans notre exemple, l'identifiant, c'est le numéro.
Mais aujourd'hui, il est important d'avoir des url qui montrent le titre de l'article comme ça les gens et les *moteurs de recherche* comprennent mieux de quoi on va parler. On va donc donner un paramètre supplémentaire : le titre adapté (pas de caractères accentués, pas d'espace), on appelle ça un `slug`.

Si on avait fait une url par défaut sur le même modèle, elle aurait valu :
`{controller}/{action}/{id}/{slug}`[^slug].
et le code aurait donné :
```csharp
routes.MapRoute(
     name: "Default",
     url: "{controller}/{action}/{id}/{slug}",
     defaults: new { controller = "Home", action="Index", id = UrlParameter.Optional, slug = UrlParameter.Optional }
);
```
Et pour afficher un tutoriel on aurait dû faire une action telle que :

```csharp
//exemple d'url = /Article/Voir/1/slug
public ActionResult Voir(int id, string slug)
{
    ViewBag.slug = slug;
    return View();
}
```
[[attention]]
|Dans les routes par défaut, le paramètre "Action" est nécessaire.

[^slug]: le mot "slug" est utilisé pour décrire une url "lisible" telle que celle de ce tutoriel. Nous verrons plus tard comment en créer un.
