Le contrôleur va jouer la jonction entre le modèle, que l'on a fait précédemment et la vue. Lorsque nous envoyons une requête au serveur, ce sont les contrôleurs qui s’occupent de la traiter. Dans un contrôleur, chaque méthode de classe représente une url. Vous allez comprendre.

Créons donc un nouveau contrôleur. Pour ce faire, créez un répertoire **Salutation** dans le répertoire Controllers. Ensuite, faites un clic-droit sur le répertoire Salutation puis Ajouter > Contrôleur…

![Ajout d'un nouveau contrôleur](/media/galleries/304/6ade8186-e234-4e09-88b9-914914c5f070.png.960x960_q85.png)

Comme nous le voyons, il existe plusieurs modèles de contrôleur. Pour l'instant, nous choisirons le **contrôleur MVC 5 - Vide**. Cliquez sur ||OK||.

![Nommer le nouveau contrôleur](/media/galleries/304/f22d55b9-ba90-4b85-b815-303e1f7a0b67.png.960x960_q85.png)

Nommons ce nouveau contrôleur **SalutationController**.

[[information]]
| Le nom d'un contrôleur doit se terminer de préférence par Controller. C'est une convention à respecter.

Visual Studio Express pour le Web nous génère le code suivant :

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Mvc;

namespace BonjourMVC.Controllers.Salutation
{
    public class SalutationController : Controller
    {
        //
        // GET: /Salutation/
        public ActionResult Index()
        {
            return View();
        }
    }
}
```

La classe générée est un peu plus difficile à comprendre qu'une classe de base. Nous noterons que la classe hérite de la classe du Framework ASP.NET MVC **Controller** ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.controller.aspx)). Il y a en plus une méthode `Index` qui retourne un objet `ActionResult` ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.actionresult(v=vs.118).aspx)), ce qui signifie que la méthode va réaliser l'action correspondant à son nom.

Dans une classe de contrôleur, chaque méthode publique représente une **action**[^action]. ASP.NET possède un mécanisme de **routage**, que nous découvrirons dans un prochain chapitre et qui permet de décrire comment interpréter l’url et d’exécuter l’action correspondante. Ainsi, lorsque que nous enverrons une requête vers la méthode **Index** de notre contrôleur **Salutation**, notre application donnera l'url suivante : **http://localhost/Salutation/Index**.

La méthode de classe du contrôleur va renvoyer une **vue** par défaut, grâce à la méthode `View()`. En fait, cette méthode va renvoyer la vue qui porte le nom par défaut **Index** et qui sera située dans le répertoire du même nom que le contrôleur.

Si nous exécutons l'application maintenant et que nous envoyons une requête vers la méthode Index du contrôleur Salutation à cette adresse http://localhost:votre_numero_de_port/Salutation/Index, le serveur ASP.NET nous affiche l'erreur suivante :

> La vue « Index » ou son maître est introuvable

Le méthode Index cherche à retourner une vue du même nom dans un répertoire similaire du répertoire **Views**. Comme nous n'avons pas encore crée de vue, il est normal que la méthode renvoie une exception.

Avant de créer une vue, il faut modifier la méthode Index pour que celle-ci réceptionne ce que saisit le visiteur et le stocke dans le modèle.

Lorsque l'on va faire appel à la méthode Index, celle-ci va instancier un objet Visiteur que l'on a créé dans les modèles. N'oublier pas d'inclure l'espace de nom `BonjourMVC.Models`.

```csharp
public class SalutationController : Controller
{
    //
    // GET: /Salutation/
    public ActionResult Index()
    {
        Visiteur client = new Visiteur();
        return View(client);
    }
}
```

Le visiteur est donc créé. Maintenant, il faut aller chercher le contenu du champ de texte et remplir la propriété `Nom` de `Visiteur` au moment du clic sur le bouton Valider. Pour cela, nous allons créer une deuxième méthode avec un attribut spécial qui va faire que cette méthode ne sera appelée que si nous cliquons sur le bouton.

Cette attribut est **AcceptVerbs** ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.acceptverbsattribute(v=vs.118).aspx)) : il dit de quelle façon nous voulons que les données soient transmises ; il y a deux manière de transmettre des données lorsque nous sommes visiteur sur un site Web : par l'url ou par formulaire. C'est pourquoi nous devons spécifier à l'attribut la façon dont nous souhaitons récupérer les données via l'énumération `HttpVerbs` ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.httpverbs(v=vs.118).aspx)).

[[information]]
|L'attribut acceptVerbs est utile quand vous désirez accepter *plusieurs* verbes. Si vous ne désirez accepter
|qu'un seul verbe (POST, GET), une version raccourcie existe `[HttpPost]`, `[HttpGet]`.

Les données utilisateur entrées via l'url sont des requêtes de type **GET** et celles entrées via les formulaires sont des requêtes de type **POST**.

```csharp
public class SalutationController : Controller
{
    //
    // GET: /Salutation/
    public ActionResult Index()
    {
        Visiteur client = new Visiteur();
        return View(client);
    }

    [AcceptVerbs(HttpVerbs.Post)]
    public ActionResult Index(Visiteur visiteur)
    {
        Visiteur client = new Visiteur();
        string prenom = "";

        prenom = Request.Form["prenom_visiteur"];
        client.Prenom = prenom;
        ViewData["message"] = "Bonjour à toi, " + prenom;
        return View("Index", client);
    }
}
```

Que de nouvelles choses ! Nous avons crée une deuxième surcharge de la méthode Index avec un paramètre qui ne nous sert à rien dans ce cas présent. Grâce à la propriété `Request.Form` ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.httprequest.form(v=vs.110).aspx)) nous récupérons la valeur de l'index placé entre croché. Ce sera le même nom d'index du côté de la vue, donc le nom du champ de texte.

Ensuite, `ViewData` ([lien MSDN](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.viewpage.viewdata(v=vs.118).aspx)) est une propriété de dictionnaire qui permet de passer des données entre le contrôleur et la vue. Nous l'avons nommé `message` et il prend pour valeur "Bonjour à toi" suivit du nom récupéré dans `Request.Form`.

La nouvelle méthode retourne la vue Index en lui passant en paramètre l'objet Visiteur avec la propriété  du modèle remplie.

Voilà pour le contrôleur, nous apercevons déjà la liaison modèle - contrôleur ; il ne nous manque plus que la vue maintenant.

[^action]: C'est très simplifié. En fait, vous pouvez dire à ASP.NET "ma méthode n'est pas une action" en utilisant l'attribut `[NonAction]`.
