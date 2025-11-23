Notre prochain cas d'étude sera le cas de l'ajout d'une image "thumbnail" pour nos articles.

Comme nous allons lier un nouvel objet à notre modèle d'article, il nous faut modifier notre classe `Article` de manière à ce qu'elle soit prête à recevoir ces nouvelles informations.

En fait la difficulté ici, c'est que vous allez transmettre un **fichier**. Un fichier, au niveau de ASP.NET, c'est représenté par l'objet `HttpPostedFileBase`. Cet objet, ne peut pas être sauvegardé avec JSON ou SQL ou tout autre méthode de sauvegarde. Ce que vous allez sauvegarder, c'est le chemin vers le fichier.

Du coup, la première idée qui vous vient c'est de rajouter une propriété dans notre class Article.

```csharp
        /// <summary>
        /// Le chemin vers le fichier image
        /// </summary>
        public string ImageName { get; set; }
```

Alors comment faire pour qu'un fichier soit téléchargé?

Une technique utilisable et que je vous conseille pour débuter, c'est de créer une nouvelle classe qu'on appelle souvent un modèle de vue[^viewmodel].
Ce *modèle de vue* est une classe normale, elle va juste être adaptée au formulaire que nous désirons mettre en place.
Créez un fichier `ArticleViewModels.cs` et à l'intérieur créez une classe "ArticleCreation".

```csharp
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Web;

namespace TutoBlog.Models
{
    public class ArticleCreation
    {
        /// <summary>
        /// Le pseudo de l'auteur
        /// </summary>
        [Required(AllowEmptyStrings = false)]
        [StringLength(128)]
        [RegularExpression(@"^[^,\.\^+$")]
        [DataType(DataType.Text)]
        public string Pseudo { get; set; }
        /// <summary>
        /// Le titre de l'article
        /// </summary>
        [Required(AllowEmptyStrings = false)]
        [StringLength(128)]
        [DataType(DataType.Text)]
        public string Titre { get; set; }
        /// <summary>
        /// Le contenu de l'article
        /// </summary>
        [Required(AllowEmptyStrings = false)]
        [DataType(DataType.Text)]
        public string Contenu { get; set; }

        /// <summary>
        /// Le fichier image
        /// </summary>
        [DisplayName("Illustration")]
        public HttpPostedFileBase Image{ get; set; }
    }
}
```

Dans votre contrôleur, nous allons réécrire la méthode **Create**. Et au lieu de demander un **Article**, nous allons demander un **ArticleCreation**.  Il faut aussi modifier notre vue **Create** pour prendre un **ArticleCreation** en entrée.

Il nous faudra aussi ajouter un champ au formulaire, qui accepte de télécharger un fichier :
```html
        <div class="form-group">
            @Html.LabelFor(model => model.Image, htmlAttributes: new { @class = "control-label col-md-2" })
            <div class="col-md-10">
                @Html.TextBoxFor(model => model.Image, new { type = "file", accept = "image/jpeg,image/png" })
                @* ou  <input type="file" name="Image"/>*@
                @Html.ValidationMessageFor(model => model.Image, "", new { @class = "text-danger" })
            </div>
        </div>
```

[[a]]
|Un formulaire, à la base, n'est pas fait pour transporter des données aussi complexes que des fichiers. Du coup, il faut les **encoder**. Et pour cela, il faut préciser un attribut de la balise `form` : `enctype="multipart/form-data"`.
|Si vous avez bien suivi les bases de Razor, vous avez compris qu'il faut modifier l'appel à la méthode `Html.BeginForm`.

Nous allons donc enregistrer le fichier une fois que ce dernier est reçu -surtout **quand** il est reçu.
La méthode SaveAs sert à cela.
Par convention, ce téléchargement se fait dans le dossier Content ou un sous dossier.
Ensuite nous allons retenir le chemin du fichier.

Attention, pour des raisons de sécurité, il est impératif d'imposer des limites à ce qui est téléchargeable.
Il est toujours conseillé de faire des vérifications dans notre contrôleur.

- une image <=> des fichiers jpeg, png ou gif;
- et dans tous les cas il faut limiter la taille du téléchargement, sur zds, 1024 Ko par exemple.


Voici ce que cela peut donner :

```csharp
        private static string[] AcceptedTypes = new string[] { "image/jpeg", "image/png" };
        private static string[] AcceptedExt = new string[] { "jpeg", "jpg", "png", "gif" };

        //POST : Create
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
                bool hasError = false;
                if (articleCreation.Image.ContentLength > 1024 * 1024)
                {
                    ModelState.AddModelError("Image", "Le fichier téléchargé est trop grand.");
                    hasError = true;
                }

                if (!AcceptedTypes.Contains(articleCreation.Image.ContentType)
                       || AcceptedExt.Contains(Path.GetExtension(articleCreation.Image.FileName).ToLower()))
                {
                    ModelState.AddModelError("Image", "Le fichier doit être une image.");
                    hasError = true;
                }

                try
                {
                    fileName = Path.GetFileName(articleCreation.Image.FileName);
                    string imagePath = Path.Combine(Server.MapPath("~/Content/Upload"), fileName);
                    articleCreation.Image.SaveAs(imagePath);
                }
                catch
                {
                    fileName = "";
                    ModelState.AddModelError("Image", "Erreur à l'enregistrement.");
                    hasError = true;
                }
                if (hasError)
                    return View(articleCreation);
            }

            Article article = new Article
            {
                Contenu = articleCreation.Contenu,
                Pseudo = articleCreation.Pseudo,
                Titre = articleCreation.Titre,
                ImageName = fileName
            };

            _repository.AddArticle(article);
            return RedirectToAction("List", "Article");
        }
```
Bien on veut afficher l'image dans notre liste d'article, pour cela il n'y a pas de helper magique dans Razor. Il faudra utiliser simplement la balise `<img />`


# Les problèmes qui se posent

Je vous présente ce cas d'étude avant de passer à la base de données pour une raison simple : un fichier, qu'il soit une image ou non, ne doit **jamais** être stocké dans une base de données.
Si vous ne respectez pas cette règle, vous risquez de voir les performances de votre site baisser de manière affolantes.

Un fichier, ça se stocke dans un **système de fichier**, pour faire plus simple, on le rangera dans un **dossier**.


## doublons

Essayons de donner à deux articles différents des images qui ont le même nom. Que se passe-t-il actuellement?

L'image déjà présente est écrasée.

Pour éviter ce genre de problèmes, il faut absolument s'assurer que le fichier qui est créé au téléchargement est **unique**.
Vous trouverez deux écoles pour rendre unique un nom de fichier, ceux qui utilisent un marquage temporel (le nombre de secondes depuis 1970) et ceux qui utiliseront un *identifiant*.

Comme nous n'utilisons pas encore de base de données, notre identifiant, c'est nous qui allons devoir le générer. Et une des meilleurs manières de faire un bon identifiant, c'est d'utiliser un *Global Unique Identifier* connu sous l'acronyme GUID.

Le code pour générer un tel GUID est simple :

```csharp
Guid id = Guid.NewGuid();
string imageFileName = id.toString()+"-"+model.Image.FileName;
```


## les caractères spéciaux

Nouveau problème : nous désirons **afficher** l'image. Pour cela, nous allons modifier le fichier de vue List pour qu'à chaque article, on ajoute une image.

Typiquement, la balise `img` s'attend à ce que vous lui donniez un lien. Comme nous avons sauvegardé notre image dans le dossier `Content/Uploads`, la balise ressemblera à : `<img src="/Content/Uploads/135435464-nomdufichier.jpg/>`.

C'est là qu'intervient le problème : vos utilisateurs n'utiliseront pas forcément des noms de fichiers qui donnent des URL sympathiques. En effet, les systèmes d'exploitation modernes savent utiliser les accents, les caractères chinois... mais pas les URL.

Pour régler Ce problème, nous allons utiliser ce qu'on appelle un **slug**.

Les slugs sont très utilisés dans les liens des sites de presse (car ils ont un impact positif sur le *SEO*[^seo]), prenons un exemple :
`nextinpact.com/news/89405-gps-europeen-deux-satellites-galileo-bien-lances-mais-mal-positionnes.htm`

Vous avez un lien en trois parties :

- `nextinpact.com` : le nom de domaine;
- `/news/` : l'équivalent pour nous du segment "{controller}";
- `89405-gps-europeen-deux-satellites-galileo-bien-lances-mais-mal-positionnes.htm` : le slug, qui permet d'écrire une url sans accent, espaces blancs... Et pour bien fait, ils ont même un identifiant unique avant.

Pour utiliser les slugs, une possibilité qui s'offre à vous est d'utiliser un package nommé *slugify*.

Dans l'explorateur de solution, cliquez-droit sur le nom du projet puis sur "gérer les packages" et installez slugify.

->![gérer les packages](/media/galleries/304/3a18c907-90c0-44e9-ac66-65fdb28eda6c.png.960x960_q85.jpg)<-

->![installer slugify](/media/galleries/304/5fcde39a-1dfe-427d-b232-e430e888f888.png.960x960_q85.jpg)<-

Pour utiliser slugify, cela se fait ainsi :

```csharp
string fileSlug = new SlugHelper().GenerateSlug(filePath);
```
[^seo]: Search Engine Optimisation : [un ensemble de techniques](http://fr.openclassrooms.com/informatique/cours/ameliorez-la-visibilite-de-votre-site-grace-au-referencement) qui permettent d'améliorer votre place dans les résultats des grands moteurs de recherche.
[^viewmodel]: En anglais on dit [ViewModel](http://stackoverflow.com/questions/11064316/what-is-viewmodel-in-mvc).
