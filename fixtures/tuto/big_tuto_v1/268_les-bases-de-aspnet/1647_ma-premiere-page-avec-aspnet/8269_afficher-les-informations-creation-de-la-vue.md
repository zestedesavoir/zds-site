La partie de l'application qui vous semblera le plus familier car nous utilisons du code HTML cette fois-ci. Comme nous vous l'avons dit, chaque méthode d'un contrôleur représente une action, liée à une vue ; pour ajouter une vue, retournons dans le code du contrôleur et faisons un clic-droit dans le code de la méthode voulu (`Index`). Visual Studio Express pour le Web nous propose d’ajouter une vue :

![Ajouter une vue depuis un contrôleur](/media/galleries/304/966b62b2-a853-4d2f-b973-dac1615fa2c7.png.960x960_q85.jpg)

Conservons le nom de vue Index, nous vous rappelons que le nom d'une vue doit être identique à celle de la méthode du contrôleur.

![Assistant d'ajout de vue](/media/galleries/304/55354a96-8232-49f4-a1f4-f63669a6f904.png.960x960_q85.png)

L'assistant nous propose de choisir un modèle pour notre vue : nous choisissons notre classe Visiteur en tant que classe de modèle pour pouvoir travailler directement avec le modèle dans la vue.

Cliquons sur ||Ajouter||. Visual Studio Express pour le Web génère le code suivant :

```html
@model BonjourMVC.Models.Visiteur

@{
    Layout = null;
}

<!DOCTYPE html>

<html>
<head>
    <meta name="viewport" content="width=device-width" />
    <title>Index</title>
</head>
<body>
    <div>
    </div>
</body>
</html>
```

Nous reconnaissons le bon vieux HTML avec cependant quelques éléments que nous n'avons jamais vu comme `@model` ou `@ { layout = null }`. Pour l'instant, disons-nous que ce sont des élément inclus dans le HTML qui interagissent avec le serveur ASP.NET.

Le fichier généré porte l'extension **.cshtml** (comme C# HTML) et est automatiquement situé dans le répertoire Views/Salutation. Nous allons maintenant garnir un peu notre page. Cela se fait en utilisant les balises HTML mais aussi avec des helper HTML qui permettent de générer le code du contrôle HTML. Par exemple, ajoutons dans la balise `<body>` la mise en forme de notre application.

![plan de notre application](/media/galleries/304/cd528be7-40e3-41e9-88c4-2e65c731b542.png)

Cette fois-ci, nous allons distinguer deux choses dans le code HTML : les éléments **statiques** que nous avons déjà vus (`<p>`, `<input>`, etc.) et les éléments **dynamiques**, qui ont une interaction avec le code serveur.

Dans notre cas, il y aura deux éléments principaux en dynamique : le champ de texte modifiable et le texte de salutation généré. Le champ de texte va associer la saisie de l'utilisateur à la clé **prenom_visiteur**, que l'on a appelé dans le contrôleur via `Request.Form`. Dans le texte de salutation, il faut afficher le **ViewData** que l'on a crée dans le contrôleur aussi.

```csharp
ViewData["message"] = "Bonjour à toi, " + prenom;
```

Voici ce que notre page **.cshtml** donne :

```html
@model BonjourMVC.Models.Visiteur

@{
    Layout = null;
}

<!DOCTYPE html>

<html>
<head>
    <meta name="viewport" content="width=device-width" />
    <title>Index</title>
</head>
<body>
    <div>
        @using (Html.BeginForm())
        {
            <h1>BonjourMVC</h1>
            <p>Comment t'appelles-tu jeune Zesteur ?</p>
            @Html.TextBox("prenom_visiteur", Model.Prenom)
            <input type="submit" value="Valider" />
        }
        <p>@ViewData["message"]</p>
    </div>
</body>
</html>
```

Nous retrouvons certains éléments que nous avons appelé dans la méthode du contrôleur. Les éléments dans le code HTML commençant par `@` sont les éléments dynamiques : c'est la syntaxe d'un moteur de vue appelé **Razor**, que nous découvrirons très bientôt.

Il y a deux **helper** HTML dans le code : `Html.BeginForm` et `Html.TextBox`. Vous l'aurez compris, ils permettent respectivement de générer un formulaire et un champ de texte modifiable. Le champ de texte portera le nom  prenom_visiteur et sera associée à la propriété Prenom de notre classe de modèle, représentée ici par la variable Model.

Après le formulaire, la balise `<p>` va contenir le message résultant. Il est temps de tester notre application maintenant !
