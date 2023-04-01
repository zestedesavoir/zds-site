Derrière le mot "interagir", se cachent en fait deux actions : l'utilisateur vous **demande** des choses ou bien l'utilisateur vous **envoie** du contenu ou en **supprime**.

Lorsqu'on navigue via navigateur, ces actions sont distinguées en deux verbes :

- GET : l'utilisateur veut juste **afficher** le contenu qui existe *déjà*. Il est important de comprendre qu'une requête qui dit "GET" ne doit **pas** modifier d'informations dans votre base de données (sauf si vous enregistrez des statistiques)
- POST : l'utilisateur **agit** sur les données ou en *crée*. Vous entendrez peut être parler des verbes `PUT` et `DELETE`. Ces derniers ne vous seront utiles que si vous utilisez le JavaScript[^js_ajax] ou bien que vous développez une API REST. En navigation basique, seul `POST` est supporté.

[[a]]
| Vous avez sûrement remarqué : je n'ai pas encore parlé de sécurité. La raison est simple, `GET` ou `POST` n'apportent **aucune** différence du point de vue sécurité.
| Si quelqu'un vous dit le contraire, c'est qu'il a sûrement mal sécurisé son site.

Passons aux formulaires. Ils sont le seul moyen que vous ayez d'obtenir des informations de la part de l'utilisateur.

Si vous deviez créer le formulaire complet en HTML, il ressemblerait à ceci :

```html
<!-- permet de créer un formulaire qui ouvrira la page zestedesavoir.com/rechercher
l'attribut method="get", permet de dire qu'on va "lister" des choses
-->
<form id="search_form" class="clearfix search-form" action="/rechercher" method="get">
    <!-- permet de créer un champ texte, ici prérempli avec "zep".-->
    <input id="id_q" type="search" value="zep" name="q"></input>
    <button type="submit"></button><!-- permet de valider le formulaire-->

</form>
```
Code: un formulaire de recherche sur ZDS[^liste_type_input]

# Particularités d'un formulaire GET

Comme vous devez lister le contenu, le formulaire GET possède quelques propriétés qui peuvent s'avérer intéressantes.

- Toutes les valeurs se retrouvent placées à la fin de l'URL sous la forme :
`url_de_base/?nom_champ_1=valeur1&nom_champ2=valeur2`;
- L'url complète (url de base + les valeurs) ne doit pas contenir plus de 255 caractères;
- Si vous copiez/collez l'url complète dans un autre onglet ou un autre navigateur : vous aurez accès au **même résultat** (sauf si la page demande à ce que vous soyez enregistré!)[^indempotence].

# Particularités d'un formulaire POST

Les formulaires POST sont fait pour envoyer des contenus nouveaux. Ils sont donc beaucoup moins limités.

- il n'y a pas de limite de nombre de caractères;
- il n'y a pas de limite de caractères spéciaux (vous pouvez mettre des accents, des smiles...);
- il est possible d'envoyer un fichier ou plusieurs fichier, seul le serveur limitera la taille du fichier envoyé.

Comme pour les formulaires `GET`, les données sont entrées sous la forme de clef=>valeur. A ceci près que les formulaires `POST` envoient les données dans la requête HTTP elle même et donc sont invisibles pour l'utilisateur lambda.
Autre propriété intéressante : si vous utilisez HTTPS, les données envoyées par POST sont cryptées. C'est pour ça qu'il est fortement conseillé d'utiliser ce protocole (quand on a un certificat[^ssl]) dès que vous demandez un mot de passe à votre utilisateur.

# Utiliser Razor pour vous aider à faire un formulaire

## Un formulaire automatisé

Comme nous l'avons déjà vu, nous pouvons entrer simplement le formulaire sous forme de code HTML dans une vue Razor.
Néanmoins, Razor vous permet de créer des formulaires complets, avec gestion des erreurs en local et côté serveur (notamment car il inclus javascript), mise en place des label et utilisation des styles css.

Pour cela, il vous faudra utiliser le *helper* `HTML.BeginForm`.

Ce *helper* est assez spécial car il embarque une vérification complète de la cohérence du formulaire, c'est pourquoi, son utilisation est particulière :

```csharp
@using(Html.BeginForm()){//créera un formulaire de type POST avec pour action celle qui a le même nom que la vue
//ici on met les champs
<button type="submit">Envoyer</button>
}
```
Code: un formulaire simple

Heureusement, vous pourrez paramétrer ce formulaire pour qu'il enclenche une action différente que celle par défaut, qu'il fasse du GET, accepte les fichiers ou encore possède un style CSS particulier.

```csharp
@using(Html.BeginForm("List", "Article",FormMethod.GET)){//créera un formulaire de type GET avec pour action Article/List
//ici on met les champs
<button type="submit">Envoyer</button>
}
```
Code: un formulaire GET

```csharp
@using(Html.BeginForm("List", "Article",FormMethod.GET, new {@class="modal pagination_form"})){//créera un formulaire de type GET avec pour action Article/List

<button type="submit">Envoyer</button>
}
```
Code: un formulaire GET avec pour classe CSS pagination_form et modal

Pour ce qui est des champs, vous pourrez alors utiliser les helpers du style `@Html.TextBox` (pour les champs input), `@Html.DropDownList` (pour les champs select), `@Html.TextArea`, `@Html.RadioButton`...

Ces champs vous seront utiles le plus souvent pour les formulaires de type GET qui seront simples et ne seront pas liés à une classe de **modèle**, comme lorsqu'on affichait des listes d'articles par exemple.


## Les formulaires basés sur un modèle de données

Parce que nous allons manipuler des données le plus souvent complexes,
nous allons -le plus souvent pour les formulaires POST, puisque ce sont ceux-là qui manipulent les données complexes- nous servir de nos classes de modèle pour construire nos formulaires.

Les formulaires razor sont très intelligents et vous permettent d'afficher rapidement :

- le champ adapté à la donnée, par exemple si vous avez une adresse mail, il vous enverra un `<input type="email"/>`;
- l'étiquette de la donnée (la balise `label`) avec le bon formatage et le bon texte;
- les erreurs qui ont été détectées lors de l'envoi grâce à javascript (attention, c'est un confort, pas une sécurité);
- les erreurs qui ont été détectées par le serveur (là, c'est une sécurité).

Pour que razor soit capable de définir le bon type de champ à montrer, il faut que vous lui donniez cette indication dans votre classe de modèle.

La classe article étant assez simpliste dans son état actuel, nous allons imaginer ce que pourrait être un formulaire de contact.

Nous allons donc créer une classe `VisitorToContact` dans les modèles.
[[secret]]
| ```csharp
|     public class VisitorToContact
|     {
|         public string Nom { get; set; }
|         public string Prenom { get; set; }
|         public DateTime Naissance { get; set; }
|         public string Email { get; set; }
|
|         public string Telephone { get; set; }
|
|         public string Message { get; set; }
|     }
| ```

Maintenant, nous allons décrire un à un les champs grâce à l'attribut `[DataType(DataType.TypeDeDonnee)]`.
Par exemple, le numéro de téléphone sera un `[DataType(DataType.PhoneNumber)]`.

[[i]]
|Il est possible de créer vos propres types de données, notamment si vous désirez automatiser la mise en place de bouton radio pour le sexe de la personne.
|Cette fonctionnalité sera présentée dans une autre partie du tutoriel.

Ensuite, dans le cas où le nom ne vous plaise pas trop (car il n'est pas assez explicite pour un visiteur, n'a pas la bonne orthographe...), vous devez ajouter l'attribut `[DisplayName("nom du label")]`.

Après modification, votre classe ressemblera à :

[[secret]]
| ```csharp
|     public class VisitorToContact
|     {
|         [DataType(DataType.Text)]
|         public string Nom { get; set; }
|         [DataType(DataType.Text)]
|         [DisplayName("Prénom")]
|         public string Prenom { get; set; }
|         [DataType(DataType.Date)]
|         [DisplayName("Date de naissance")]
|         public DateTime Naissance { get; set; }
|         [DataType(DataType.EmailAddress)]
|         public string Email { get; set; }
|         [DataType(DataType.PhoneNumber)]
|         [DisplayName("Numéro de téléphone")]
|         public string Telephone { get; set; }
|         [DataType(DataType.MultilineText)]
|         public string Message { get; set; }
|     }
| ```

Dans le contrôleur Home, nous allons ajouter une méthode `Contact(VisitorToContact visitor)` :
```csharp
public ActionResult Contact(VisitorToContact visitor)
{
    return View(visitor);
}
```

Maintenant, nous allons modifier la vue `Home\Contact.cshtml`.

La première action à faire sera d'indiquer à la vue que si modèle il y a, ce sera un modèle de type `VisitorContact`.
Pour cela, faites en sorte que `@model TutoBlog.Models.VisitorToContact` soit placé en première ligne.

Et maintenant, créons notre formulaire !

Comme nous avons un modèle, nous pouvons laisser Razor générer tout seul les champs à utiliser ainsi que les label et les messages d'erreur quand il y en a.

Pour cela, trois *helpers* à retenir (et uniquement trois !!) :

- `Html.LabelFor(model=>model.champ)` pour le label (exemple `Html.LabelFor(model => model.Email)`)
- `Html.EditorFor(model=>model.champ)` pour le champ (exemple `Html.EditorFor(model => model.Email)`)
- `Html.ValidationMessageFor(model=>model.champ)` pour le message d'erreur(exemple `Html.ValidationMessageFor(model => model.Email)`)

[[i]]
| A noter, vous pourrez aussi trouver, au début du formulaire `Html.ValidationSummary(true)`

Comme pour le formulaire, vous pouvez *customiser* chacun des trois helper en utilisant une surcharge qui a un argument appelé **htmlattributes**.

Je vous laisse essayer de faire ce formulaire vous même.
Il est absolument nécessaire que vous ne **copiez pas** la correction avant d'avoir compris.

A noter que Visual studio sait que faire un formulaire, c'est répétitif alors il possède un tas de moyens d'automatiser leur génération.
C'est cette fonctionnalité que nous utiliserons par la suite, mais gardez à l'esprit que vous **devez** savoir faire seul un formulaire pour réussir à vous en sortir !

## Correction

[[secret]]
|
| ```razor
| @model TutoBlog.Models.VisitorToContact
|
| @{
|     ViewBag.Title = "Contact";
| }
| <h2>@ViewBag.Title.</h2>
|
| @using (Html.BeginForm())
| {
|     <div class="form-horizontal">
|         @Html.ValidationSummary(true, "", new { @class = "text-danger" })
|         <div class="form-group">
|             @Html.LabelFor(model => model.Nom, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Nom, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Nom, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <div class="form-group">
|             @Html.LabelFor(model => model.Prenom, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Prenom, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Prenom, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <div class="form-group">
|             @Html.LabelFor(model => model.Telephone, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Telephone, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Telephone, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <div class="form-group">
|             @Html.LabelFor(model => model.Naissance, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Naissance, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Naissance, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <div class="form-group">
|             @Html.LabelFor(model => model.Email, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Email, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Email, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <div class="form-group">
|             @Html.LabelFor(model => model.Message, htmlAttributes: new { @class = "control-label col-md-2" })
|             <div class="col-md-10">
|                 @Html.EditorFor(model => model.Message, new { htmlAttributes = new { @class = "form-control" } })
|                 @Html.ValidationMessageFor(model => model.Message, "", new { @class = "text-danger" })
|             </div>
|         </div>
|         <button type="submit">Envoyer</button><button type="reset">Réinitialiser</button>
|     </div>
| }
| ```

[^js_ajax]: une technique avancée mais néanmoins courante dans le web moderne est l'utilisation de JavaScript avec l'objet XMLHttpRequest. L’acronyme qui désigne cette utilisation est *AJAX*.
[^liste_type_input]: la liste complète des types de champ HTML se trouve [ici](http://www.alsacreations.com/tuto/lire/1372-formulaires-html5-nouveaux-types-champs-input.html).
[^indempotence]: On parle d'[indempotence](http://fr.wikipedia.org/wiki/Idempotence#En_informatique).
[^ssl]: le protocole HTTPS garantie la confidentialité (i.e ce qui est transmis est secret) et l'authenticité (i.e que le site est bien qui il prétend être) et pour cela il faut acheter un [certificat](http://fr.wikipedia.org/wiki/Certificat_%C3%A9lectronique).
