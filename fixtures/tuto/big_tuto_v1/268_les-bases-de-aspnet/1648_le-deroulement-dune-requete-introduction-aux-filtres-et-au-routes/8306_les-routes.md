# Allons plus loin avec les routes par défaut

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

Par contre "id" est un paramètre qui est propre à notre application.
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

Prenons un exemple : [les tutoriels de zeste de savoir](http://zestedesavoir.com/tutoriels).

vous avez deux types d'url:

- /tutoriels/
- /tutoriels/un_numero/le_titre

Pour les auteurs, nous avons la même chose du côté de l'édition.

Dans notre exemple, l'identifiant, c'est le numéro. Le titre du tutoriel est un paramètre ajouté qui sert à améliorer le référencement du site.
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
//exemple d'url = /Home/Voir/1/slug
public ActionResult Voir(int id, string slug)
{
    ViewBag.slug = slug;
    return View();
}
```
[[attention]]
|Dans les routes par défaut, le paramètre "Action" est nécessaire.

# Les routes personnalisées

Reprenons l'exemple de zeste de savoir, mais cette fois-ci, allons du côté des [forums](http://zestedesavoir.com/forums).
Ces derniers sont organisés d'une manière spéciale, en effet, vous avez la liste des forums qui est divisée en deux catégories. Puis, dans ces catégories vous avez une liste de sous catégorie.

Pour lister tous les messages, vous n'avez pas une url du style `souscategorie/un_numero/un_titre` mais `forums/titre_categorie/titre_sous_categorie`.

Ce genre d'url est très complexe à généraliser, alors il faudra personnaliser ça au niveau du contrôleur.

Je vous invite à créer un contrôleur que nous appelleront **ForumControlleur**.
Dans ce contrôleur, nous allons créer une action Index qui prend deux paramètres de type string `slug_category`, `slug_sub_category` et une vue Index.cshtml qui est vide.
Essayons d'accéder à l'url `http://llocalhost:port/Forum/Index/cat/subcat` :

![page introuvable ](/media/galleries/304/afc625eb-3fd5-44fb-8f9c-759550cc5e37.png.960x960_q85.png)

Par contre, il est capable de trouver `http://localhost:port/Forum/Index/?slug_category=cat&slug_sub_category=subcat`.

Comme il n'a pas trouvé de paramètre qui colle avec sa route par défaut, il a interprété tous les autres paramètres de votre fonction comme des *query string*.
Pour faire plus beau, nous allons lui dire qu'il doit router l'url par segment grâce à un attribut qui s'appelle `Route` et qui se place au dessus de la fonction :
```csharp
[Route("Forum/Index/{slug_category}/{slug_sub_category}")]
public ActionResult Index(string slug_category, string slug_sub_category)
{
    return View();
}
```
Puis, dans RouteConfig.cs, nous allons lui dire que quand il voit l'attribut `Route`, il doit utiliser la route définie :
```csharp
public static void RegisterRoutes(RouteCollection routes)
{
    routes.IgnoreRoute("{resource}.axd/{*pathInfo}");
    routes.MapMvcAttributeRoutes();
    routes.MapRoute(
        name: "Default",
        url: "{controller}/{action}/{id}",
        defaults: new { controller = "Home", action = "Index", id = UrlParameter.Optional }
    );
}
```
