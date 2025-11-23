Comme nous l'avons vu dans la première partie, lorsque l'utilisateur veut obtenir une page, il envoie une *requête* au serveur.
Le premier défi du serveur sera de comprendre quel contrôleur vous désirez utiliser et quelle action vous désirez faire. Une **action** est simplement une méthode d'une classe de contrôleur.

Cette étape s'appelle le **routage**[^route].

Une fois que le serveur sait quelle action il doit appeler, il va regarder s'il a le droit de l'appeler : la requête va passer par des **filtres**.

Si les filtres acceptent tous la requête, l'action est appelée. A la fin de celle-ci vous allez générer une page grâce au moteur de template.

D'autres filtres vérifieront que le résultat est bon et si tout va bien, le visiteur verra sa page HTML.

-> ![Exécution d'un site](/media/galleries/304/46cac8ac-fca7-4d13-8cf6-153ec1be3e90.png.960x960_q85.jpg) <-

[[question]]
|Mais pour l'instant, on n'a jamais parlé de route ou de filtre, alors pourquoi ça marche bien?

L'avantage de l'architecture MVC, c'est qu'elle est plutôt bien *normalisée*, du coup, quand vous avez créé votre projet, Visual Studio **savait** qu'il fallait configurer le routage de manière à ce que toute url de la forme `nom du contrôleur/nom de l'action` soit bien routé. Souvenez-vous du chapitre précédent avec l'exemple du BonjourMVC, nous avons appelé un contrôleur et chaque méthode de ce contrôleur renvoyait une vue. Au final, nous avions un url de ce type : /Salutation/Index avec Salutation le nom du contrôleur et Index la méthode.

Visual Studio a donc, pour vous, généré un petit code qui se trouve dans le dossier **App_Start**, et plus précisément dans le fichier `FilterConfig.cs` et `RouteConfig.cs`.

```csharp
public class RouteConfig
{
    public static void RegisterRoutes(RouteCollection routes)
    {
        routes.IgnoreRoute("{resource}.axd/{*pathInfo}");

        routes.MapRoute(
            name: "Default",
            url: "{controller}/{action}/{id}",
            defaults: new { controller = "Home", action = "Index", id = UrlParameter.Optional }
        );
    }
}
```

Code: RouteConfig.cs

```csharp
public class FilterConfig
{
    public static void RegisterGlobalFilters(GlobalFilterCollection filters)
    {
        filters.Add(new HandleErrorAttribute());
    }
}
```

Code: FilterConfig.cs

Dans ces deux fichiers, vous aurez les conventions de nommage pour les routes et les filtres qui s'appliquent dans **toute votre application**.

[[question]]
|Et si je veux faire une route spéciale juste à un endroit?

La partie suivante est faite pour vous.

[^route]: à ne pas confondre avec le routage réseau qui n'a rien à voir.
