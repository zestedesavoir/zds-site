# Envoyer des données avec un formulaire

Lorsque vous désirez demander à un utilisateur d'entrer des données (par exemple le titre et le contenu de l'article), vous devez utiliser un **formulaire**.

Du point de vue HTML, un formulaire est représenté par la balise `<form>`.

Un formulaire peut envoyer les données de deux manières différentes, en utilisant deux verbes HTTP différents : GET et POST.

Souvent on utilise les formulaire GET quand on veut filtrer une liste alors qu'on utilise les formulaires POST pour ajouter, modifier ou supprimer du contenu.

## Les formulaires GET

Les formulaires de type GET redirigent vers une url du type `/controller/action/?parametre1=valeur1&parametre2=valeur2`.

Pour y répondre vous n'avez qu'à créer une action qui prenne les paramètres en tant qu'argument :
```csharp
        [HttpGet]
        public ActionResult List(string order, DateTime limitDate)
        {
            return View();
        }
```
Code: Une action qui répond à un GET

Le formulaire qui permet d'entrer ces données sera :

```csharp
    @using (Html.BeginForm("List", "Forum", FormMethod.Get)) {
        @Html.TextBox("limitDate", DateTime.Now.ToString())
        @Html.DropDownList("order", new SelectListItem[]{
                new SelectListItem{Value = "Asc", Text ="Ordre croissant"},
                new SelectListItem{Value = "Desc", Text ="Ordre décroissant"}
        })
    }
```

## Les formulaires POST

Pour créer des données, nous allons utiliser des formulaires POST.
Afin de faciliter le travail de vérification et de routage, nous allons devoir créer une classe de "modèle".

Dans le dossier "Model", si vous n'avez pas de classe Article, créez la.
Pour faire simple, nous allons demander deux choses à la classe article : un titre et un corps.

Créons un contrôleur avec action en lecture et écriture pour cette  classe. Jetons un coup d'oeil à la méthode Create :

```csharp
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
```
Par défaut, VisualStudio vous propose de gérer un FormCollection.
Cela vous permet de gérer un formulaire totalement personnalisé. Nous l'utiliserons plus tard, quand nous irons plus loin. Pour l'instant, nous allons faire les choses simplement. Et comme nous savons que notre formulaire doit nous envoyer un article, nous allons faire fi de la FormCollection pour utiliser un Article :

```csharp
 public ActionResult Create(Article article)
```

Maintenant, allons nous créer une vue. Dans le dossier `View\Nom de votre contrôleur`, cliquez droit, ajouter, Vue.

->![Ajouter vue](/media/galleries/304/fc5a1a01-34ca-45b3-b090-6ff938d725e0.png.960x960_q85.jpg)<-

Appelez-la `Create`. Dans Modèle sélectionnez `Create`, dans classe de modèle sélectionnez `Article` puis validez.

->![configurer vue](/media/galleries/304/fb387003-5d68-4b2a-8ceb-ea2512134e57.png.960x960_q85.png)<-

Visual studio aura créé pour vous le formulaire :

```csharp
@using (Html.BeginForm())
{
    @Html.AntiForgeryToken()

    <div class="form-horizontal">
        <h4>Article</h4>
        <hr />
        @Html.ValidationSummary(true, "", new { @class = "text-danger" })
        <div class="form-group">
            @Html.LabelFor(model => model.Titre, htmlAttributes: new { @class = "control-label col-md-2" })
            <div class="col-md-10">
                @Html.EditorFor(model => model.Titre, new { htmlAttributes = new { @class = "form-control" } })
                @Html.ValidationMessageFor(model => model.Titre, "", new { @class = "text-danger" })
            </div>
        </div>

        <div class="form-group">
            @Html.LabelFor(model => model.Corps, htmlAttributes: new { @class = "control-label col-md-2" })
            <div class="col-md-10">
                @Html.EditorFor(model => model.Corps, new { htmlAttributes = new { @class = "form-control" } })
                @Html.ValidationMessageFor(model => model.Corps, "", new { @class = "text-danger" })
            </div>
        </div>

        <div class="form-group">
            <div class="col-md-offset-2 col-md-10">
                <input type="submit" value="Create" class="btn btn-default" />
            </div>
        </div>
    </div>
}
```

Ce formulaire sait absolument tout faire !

Il vous affiche les bons label, les bons champs... Et en plus il vous protège d'une faille : la faille appelée *CSRF*.

Cette faille est une faille qui permet à des sites extérieurs d'envoyer des données sur votre site sans passer par lui et donc a priori de faire des choses mauvaises.

Elle fonctionne comme ça :

Imaginez vous, vous êtes l'administrateur de votre blog. Alors vous vous y connectez en tant qu'administrateur.

En même temps, vous visitez d'autres sites dans les autres onglets de votre navigateur. L'un d'entre eux veux vous jouer un mauvais tour. Du coup il va tenter de vous rediriger vers votre propre blog en envoyant automatiquement une requête POST. Comme vous êtes connecté, les sécurités passent et vous avez mis des mauvaises choses sur votre blog.

La ligne `@Html.AntiForgeryToken()` empêche ça. Par contre elle vous oblige à signaler cela à votre contrôleur.

Pour faire cela, nous allons devoir utiliser un filtre qui s'appelle `ValidateAntiForgeryTokenAttribute`. Du coup la méthode `Create` ressemble à ça :

```csharp
[HttpPost]
[ValidateAntiForgeryToken]
public ActionResult Create(Article article)
```



# Envoyer une image avec un formulaire
