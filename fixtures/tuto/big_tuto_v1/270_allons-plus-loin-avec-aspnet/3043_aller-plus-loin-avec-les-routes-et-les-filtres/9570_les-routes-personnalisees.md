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
