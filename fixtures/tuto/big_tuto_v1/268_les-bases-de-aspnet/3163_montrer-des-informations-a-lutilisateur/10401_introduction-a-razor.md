Les vues sont le point le plus important pour l’utilisateur de votre application. En effet, un visiteur se fiche bien de l’organisation de la logique de notre application Web (bien que ce soit important pour nous, développeur) : le seul composant qu’il verra et pourra juger est la vue. Les vues sont donc essentielles, elles doivent être agréables et ergonomiques pour le visiteur et d’un autre côté maintenables et lisibles pour le développeur.

Evidemment, nous ne vous conseillons pas de mettre de côté l’architecture et l’organisation de la logique des contrôleurs. Le code doit rester maintenable et bien pensé.

# Bonjour Razor !

ASP.NET MVC utilise un moteur de vues appelé Razor. Comme son nom l’indique, un moteur de vues permet la création de vues (de pages HTML). Le moteur de vues va communiquer avec le code « serveur » afin de générer une réponse au format HTML. Le moteur de templates Razor est apparu avec le version 3 de ASP.NET MVC, c’est le moteur de templates par défaut avec ASP.NET MVC. Razor utilise sa propre syntaxe, l’avantage c’est que celle-ci a pour vocation d’être simple et de faciliter la lecture des pages de vues pour le développeur. Nous retrouvons une fluidification entre code HTML et code exécutable.
Pour une application utilisant le C#, les vues Razor porterons l’extension **.cshtml**, mais si vous utilisez VB.NET, l’extension **.vbhtml** sera utilisée.

Nous considèrerons même cela comme un moteur de conception et de composition de gabarits (**Template** en anglais).

[[information]]
|Un gabarit (ou template) est un modèle de document (HTML) amené à être modifié. Une application Web dynamique utilise les gabarits pour générer une page HTML (afficher votre pseudonyme, lister les derniers billets d’un blog, etc.).

Le moteur de templates Razor (et nous utiliserons dorénavant ce terme) offre un pseudo-langage, avec une syntaxe propre à lui pour permettre la séparation du code C# du code HTML tout en conservant une interaction avec la logique serveur (le HTML étant un langage de description côté client).

# Syntaxe de Razor

Découvrons maintenant les rudiments de la syntaxe que nous offre Razor. Nous distinguons deux types de syntaxe utilisables avec Razor :

- Les instructions uniques ;
- les blocs de code

Le code Razor s’écrit directement dans le code HTML.

[[information]]
| Nous parlons de code Razor, mais en vérité cela reste du code C#. Razor propose une syntaxe permettant de s'inclure directement dans le balisage HTML.

#### Les instructions uniques

Une instruction unique se fait avec le symbole arobase "```@```". Par exemple pour afficher la date courante :

```csharp
<p>Bienvenue sur mon blog, nous sommes le @DateTime.Now</p>
```
Avec, vous l’aurez reconnu, l’objet DateTime donnant des informations sur le temps. Une instruction unique va directement générer du contenu au sein du code HTML, elle tient sur une ligne.

#### Les blocs de code

Le second type de syntaxe Razor est le bloc de code. Comme son nom l’indique, un bloc de code est une section qui va contenir exclusivement du code Razor, sans HTML. Comme tout bloc en programmation, celui-ci est délimité par des symboles marquant le début et la fin du bloc d’instructions.

Un bloc de code est délimité par le symbole arobase et d’une paire d’accolades : le début du bloc, nous trouvons les signes "```@{```" et le signe "```}```" à la fin du bloc.

Tout ce qui se situe entre ces délimiteurs doivent respecter les règles du langage de programmation utilisé, c’est-à-dire le C#. Une page de vue écrite avec Razor respecte les mêmes règles qu’un fichier source C#.

### Exemple

Dans notre application de blog, créons un nouveau contrôleur vide. Nous l'appellerons **DemoController**.

```csharp
public class DemoController : Controller
{
    //
    // GET: /Demo/
    public ActionResult Index()
    {
        return View();
    }
}
```

A l'aide du clique droit, ajoutons une vue appelée **Index**.

```html

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

En haut du code HTML, nous trouvons déjà une instruction Razor définie dans un bloc de code @{ }.

```html
@{
    Layout = null;
}
```

Layout est une variable initialisé à null car nous n'utilisons pas de mise en page particulière. Nous reviendrons sur les mises en pages très prochainement. Dans la balise ```<div>``` ajoutons le code suivant :

```html
<body>
    <div>
        @{
            String nom = "Clem";
            String message = "Salut " + nom;
        }

        <p>@message</p>
    </div>
</body>
```

Nous créons une variable contenant "Clem" et une autre concaténant la valeur de la variable ```nom``` avec "Salut". Ensuite, nous demandons d'accéder à la valeur de la variable dans le paragraphe ```<p></p>```. Ce qui donne :

![Afficher la vue dans le navigateur](/media/galleries/304/00cbecf2-8e22-4bd9-9b6d-9555a8ed3cc7.png.960x960_q85.jpg)

![résultat de la vue](/media/galleries/304/af0a96c2-af4c-4755-bec1-7546ee87f392.png.960x960_q85.png)
