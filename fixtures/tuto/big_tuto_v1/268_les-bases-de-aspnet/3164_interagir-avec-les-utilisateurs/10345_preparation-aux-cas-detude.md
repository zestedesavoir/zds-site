Dans les sections suivantes, nous allons échanger des données avec nos utilisateurs. Pour cela, quatre cas d'études sont prévus :

- afficher vos articles
- la création d'un article;
- l'envoie d'une image.
- la sélection d'une page parmi plusieurs (appelé la pagination)

Pour que ces cas d'études se passent de la meilleure des manières, il faudra préparer votre espace de travail.

Comme nous allons manipuler des "articles", il faudra commencer par définir ce qu'est un article. Pour faire simple, nous allons supposer qu'un article possède les *propriétés* suivantes :

- le pseudo de son auteur
- le titre de l'article
- le texte de l'article

Dans le dossier `Models`, créez la classe suivante :

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace Blog.Models
{
    /// <summary>
    /// Notre modèle de base pour représenter un article
    /// </summary>
    public class Article
    {
        /// <summary>
        /// Le pseudo de l'auteur
        /// </summary>
        public string Pseudo { get; set; }
        /// <summary>
        /// Le titre de l'article
        /// </summary>
        public string Titre { get; set; }
        /// <summary>
        /// Le contenu de l'article
        /// </summary>
        public string Contenu { get; set; }
    }
}
```

Pour aller plus vite, je vous propose un exemple de liste d'article au format JSON. Ce fichier permet de stocker ses articles, nous utiliserons la base de données dans le prochain chapitre.

Téléchargez le [fichier](https://onedrive.live.com/redir?resid=598BC65CD25E0735!2581&authkey=!AC5VhEAGFqfDjIk&ithint=file%2cjson), placez-le dans le dossier App_Data.
Puis, pour qu'il apparaisse dans visual studio, cliquez-droit sur le dossier App_Data, et "Ajouter un élément existant". Sélectionnez le fichier.

Il est extrêmement facile de lire un fichier de ce type contrairement à un fichier texte. JSON est un format de données textuelles, tout comme le XML. Il est très répandu dans le monde du développement web.
Le contenu d'un fichier JSON ressemble à cela :

```js
{
    "post": {
        "pseudo": { "value": "Clem" },
        "titre": { "value": "mon article" },
        "contenu": { "value": "Du texte, du texte, du texte" }
    }
}
```

Maintenant, nous allons utiliser un outil qui est capable de lire le JSON.  Pour cela, nous allons utiliser un package, cliquez-droit sur le nom du projet puis "Gérer les packages nuget". Cherchez JSON.NET et installez-le.

Pour ceux qui veulent savoir ce qu'est [NuGet](https://www.nuget.org/), c'est simplement une bibliothèque de package, il regroupe plein de librairies et DLL pour la plateforme de développement sous Microsoft.

-> ![Installez JSON.NET](/media/galleries/304/148bda87-d5fc-46bd-af03-440058602f67.png.960x960_q85.png) <-

Ensuite, dans le dossier `Models` créez le fichier `ArticleJSONRepository.cs` et entrez ce code :

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using Newtonsoft.Json;
using System.IO;

namespace Blog.Models
{
    /// <summary>
    /// permet de gérer les articles qui sont enregistrés dans un fichier JSON
    /// </summary>
    public class ArticleJSONRepository
    {
        /// <summary>
        /// Représente le chemin du fichier JSON
        /// </summary>
        private readonly string _savedFile;

        /// <summary>
        /// Construit le gestionnaire d'article à partir du nom d'un fichier JSON
        /// </summary>
        /// <param name="fileName">nom du fichier json</param>
        public ArticleJSONRepository(string fileName)
        {
            _savedFile = fileName;
        }

        /// <summary>
        /// Obtient un unique article à partir de sa place dans la liste enregistrée
        /// </summary>
        /// <param name="id">la place de l'article dans la liste (commence de 0)</param>
        /// <returns>L'article désiré</returns>
        public Article GetArticleById(int id)
        {
            using (StreamReader reader = new StreamReader(_savedFile))
            {
                List<Article> list = JsonConvert.DeserializeObject<List<Article>>(reader.ReadToEnd());

                if (list.Count < id || id < 0)
                {
                    throw new ArgumentOutOfRangeException("Id incorrect");
                }
                return list[id];
            }

        }

        /// <summary>
        /// Obtient une liste d'article
        /// </summary>
        /// <param name="start">Premier article sélectionné</param>
        /// <param name="count">Nombre d'article sélectionné</param>
        /// <returns></returns>
        public IEnumerable<Article> GetListArticle(int start = 0, int count = 10)
        {
            using (StreamReader reader = new StreamReader(_savedFile))
            {
                List<Article> list = JsonConvert.DeserializeObject<List<Article>>(reader.ReadToEnd());
                return list.Skip(start).Take(count);
            }
        }

        /// <summary>
        /// Obtient une liste de tout les articles
        /// </summary>
        public IEnumerable<Article> GetAllListArticle()
        {
            using (StreamReader reader = new StreamReader(_savedFile))
            {
                List<Article> list = JsonConvert.DeserializeObject<List<Article>>(reader.ReadToEnd());
                return list;
            }
        }

        /// <summary>
        /// Ajoute un article à la liste
        /// </summary>
        /// <param name="newArticle">Le nouvel article</param>
        public void AddArticle(Article newArticle)
        {
            List<Article> list;
            using (StreamReader reader = new StreamReader(_savedFile))
            {
                list = JsonConvert.DeserializeObject<List<Article>>(reader.ReadToEnd());
            }
            using (StreamWriter writter = new StreamWriter(_savedFile, false))
            {
                list.Add(newArticle);
                writter.Write(JsonConvert.SerializeObject(list));
            }
        }
    }
}
```

Avec le code ci-dessus nous allons pouvoir récupérer nos articles qui se trouvent dans notre ficher JSON et pouvoir en créer. Les méthodes parlent d'elles-mêmes : nous lisons et écrivons dans le fichier JSON.
