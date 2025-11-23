Bien, maintenant, nous avons nos articles avec leurs commentaires. C'est une bonne chose, et sachez que la relation One To Many est la plus courante dans le monde de la base de données.

# Définition et mise en place

Pour autant elle n'est pas la seule à être très utilisée, nous allons le découvrir grâce à ce nouveau cas d'étude qui concerne les Tag.

Avant d'aller plus loin, essayons de comprendre ce qu'est un Tag et son intérêt.

Basiquement, un tag c'est un mot clef ou une expression clef. Ce mot clef permet de regrouper un certain nombre de contenu sous son égide. Mais comme ce n'est qu'un mot clef, et non une catégorie hiérarchique, un article peut se référer à plusieurs mots clefs.

Prenons un exemple avec ce tutoriel, il se réfère aux mots clefs `.NET`, `Web Service` et `C#`. En effet, nous avons utilisé le C# pour créer un Web Service à partir du framework .NET. On dit que grâce aux tag, on navigue de manière *horizontale* plutôt que *hiérarchique* (ou *verticale*). En effet, quelqu'un qui lit notre tutoriel peut se vouloir se renseigner plus à propos de ce qu'il se passe dans le framework .NET et ira sûrement obtenir d'autres tutoriels pour faire une application Windows Phone, un navigateur avec Awesomium...

Vous l'aurez compris, un article possède plusieurs tags mais chaque tag pointe vers plusieurs articles. On dit alors que la relation entre les deux entités est une relation Many To Many.

![Liaison many to many](http://zestedesavoir.com/media/galleries/304/8c06c41e-9a59-43a1-b4a7-384427095847.png.960x960_q85.jpg)

L'idée sera donc, du point de vue du code, de simplement créer dans la classe article une liste de tag et dans la classe Tag une liste d'Articles.

```csharp
    public class Tag
    {
        public int ID { get; set; }

        public string Name { get; set; }

        [StringLength(255)]
        [Display(AutoGenerateField = true)]
        [Index(IsUnique=true)]//permet de rendre unique le slug comme ça le tag "Mon Tag" et "mon tag" et "MOn Tag" seront le même :-)
        public string Slug { get; set; }
        public virtual List<Article> LinkedArticles { get; set; }
    }

    public class Article
    {
        public int ID { get; set; }
        /// <summary>
        /// Le pseudo de l'auteur
        /// </summary>
        [Required(AllowEmptyStrings = false)]
        [StringLength(128)]
        [RegularExpression(@"^[^,\.\^]+$")]
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
        [DataType(DataType.MultilineText)]
        public string Contenu { get; set; }

        /// <summary>
        /// Le chemin de l'image
        /// </summary>
        public string ImageName { get; set; }

        public virtual List<Commentaire> Comments { get; set; }
        public virtual List<Tag> Tags { get; set; }
    }
```
Code: Les classes Tag et Article

[[i]]
|Vous l'avez peut-être remarqué, j'ai utilisé l'attribut `[Index]`. Ce dernier permet de spécifier que notre Slug sera unique dans la bdd ET qu'en plus trouver un tag à partir de son slug sera presque aussi rapide que de le trouver par sa clef primaire.

Dans notre base de données, nous aurons par contre un léger changement. Allons voir notre explorateur de serveur une fois que la classe Tag a été ajoutée à notre DbContext.

![L'explorateur de serveur](http://zestedesavoir.com/media/galleries/304/218e0ef6-4f06-41b2-9ee5-988197e369ca.png.960x960_q85.png)

Nous observons qu'une nouvelle table a été ajoutée, je l'ai encadrée pour vous. Elle a été automatiquement nommée "TagArticle" et permet de faire le lien entre les articles et les tags. En fait lorsque vous ajouterez un tag à un article, c'est dans cette table que l'entrée sera enregistrée. Et cette entrée sera l'identifiant de votre article en première colonne et celui du tag lié en seconde colonne.

[[i]]
|Retenez bien cela : toute relation many to many crée en arrière plan une nouvelle table. Mais ne vous inquiétez pas, dans bien des cas cette table n'impacte pas les performances de votre site, en fait si vous avez bien réfléchi, cela va même les améliorer car la bdd est faite **pour ça** !

# Un champ texte, des virgules

Notre but, désormais, sera, à la création de l'article, de choisir une liste de Tags. Comme le nombre de tags est indéterminé au départ, on ne peut pas proposer 5 ou 10 cases juste pour rentrer des tags, le mieux, c'est de proposer un champ texte simple et de dire que chaque tag sera séparé par une virgule.

Je vous rappelle que le modèle d'article nécessite un *ViewModel* pour traiter facilement les données d'image. Le meilleur moyen d'arriver à nos fins est donc de continuer le travail de ce *ViewModel* pour réussir à traiter notre liste de tags.

Je mets le code "final" en caché, mais voici ce qu'il vous faudra faire :

1. Modifier le ViewModel pour qu'il accepte une **chaîne de caractères** nommée "Tags" qui s'affiche correctement;
2. Modifier le contrôleur pour qu'il récupère les tags qu'on veut ajouter
3. Ensuite il doit regarder en bdd ceux qui existent déjà
4. Pour pouvoir ajouter ceux qui n'existent pas en bdd
5. Et enfin tout lier à l'article qu'on vient de créer !

[[secret]]
| ```csharp
|         [HttpPost]
|         [ValidateAntiForgeryToken]
|         public ActionResult Create(ArticleCreation articleCreation)
|         {
|             if (!ModelState.IsValid)
|             {
|                 return View(articleCreation);
|             }
|
|             string fileName = "";
|             if (!handleImage(articleCreation, out fileName))
|             {
|                 return View(articleCreation);
|             }
|
|             Article article = new Article
|             {
|                 Contenu = articleCreation.Contenu,
|                 Pseudo = articleCreation.Pseudo,
|                 Titre = articleCreation.Titre,
|                 ImageName = fileName,
|                 Tags = new List<Tag>()
|             };
|             IEnumerable<Tag> askedTags = new List<Tag>();
|
|             SlugHelper slugifier = new SlugHelper();
|             if(articleCreation.Tags.Trim().Length > 0)
|             {
|                 askedTags = from tagName in articleCreation.Tags.Split(',') select new Tag { Name = tagName.Trim(), Slug = slugifier.GenerateSlug(tagName.Trim()) };
|             }
|             foreach (Tag tag in askedTags)
|             {
|                 Tag foundInDatabase = bdd.Tags.FirstOrDefault(t => t.Slug == tag.Slug);
|                 if (foundInDatabase != default(Tag))
|                 {
|                     article.Tags.Add(foundInDatabase);
|                 }
|                 else
|                 {
|                     article.Tags.Add(tag);
|                 }
|             }
|
|             bdd.Articles.Add(article);
|
|             bdd.SaveChanges();
|             return RedirectToAction("List", "Article");
|         }
| ```
| Code: La méthode Create du contrôleur avec les tags.

Si vous avez réussi à produire un code similaire à la correction que je vous propose, bravo!

Vous allez pouvoir faire la même chose pour la fonction d'édition. Par contre, faites attention, il faudra en plus prendre en compte que le fait que le tag a peut être déjà été ajouté à l'article.

[[secret]]
| ```csharp
|         [HttpPost]
|         [ValidateAntiForgeryToken]
|         public ActionResult Edit(int id, ArticleCreation articleCreation)
|         {
|             //on ne peut plus utiliser Find car pour aller chercher les tags nous devons utiliser Include.
|             Article entity = bdd.Articles.Include("Tags").FirstOrDefault(m => m.ID == id);
|             if (entity == null)
|             {
|                 return RedirectToAction("List");
|             }
|             string fileName;
|             if (!handleImage(articleCreation, out fileName))
|             {
|
|                 return View(articleCreation);
|             }
|             DbEntityEntry<Article> entry = bdd.Entry(entity);
|             entry.State = System.Data.Entity.EntityState.Modified;
|             Article article = new Article
|             {
|                 Contenu = articleCreation.Contenu,
|                 Pseudo = articleCreation.Pseudo,
|                 Titre = articleCreation.Titre,
|                 ImageName = fileName
|             };
|             entry.CurrentValues.SetValues(article);
|             IEnumerable<Tag> askedTags = new List<Tag>();
|
|             SlugHelper slugifier = new SlugHelper();
|             if (articleCreation.Tags.Trim().Length > 0)
|             {
|                 askedTags = from tagName in articleCreation.Tags.Split(',') select new Tag { Name = tagName.Trim(), Slug = slugifier.GenerateSlug(tagName.Trim()) };
|             }
|
|             foreach (Tag tag in askedTags)
|             {
|                 Tag foundInDatabase = bdd.Tags.FirstOrDefault(t => t.Slug == tag.Slug);
|                 if (foundInDatabase != default(Tag) && !article.Tags.Contains(foundInDatabase))
|                 {
|                     article.Tags.Add(foundInDatabase);
|                 }
|                 else if(foundInDatabase == default(Tag))
|                 {
|                     article.Tags.Add(tag);
|                 }
|             }
|
|             bdd.SaveChanges();
|
|             return RedirectToAction("List");
|         }
| ```
| Code: La méthode d'édition avec la prise en charge des tags

[[i]]
|Vous l'aurez peut-être remarqué, nous avons plusieurs fois dupliqué du code. Je sais, c'est mal !
|Ne vous inquiétez, pas nous y reviendront. En effet, pour simplifier énormément notre code, nous allons devoir apprendre comment créer nos propres validateurs, ainsi que la notion de ModelBinder. Cela sera fait dans la prochaine partie.

# Allons plus loin avec les relations Plusieurs à Plusieurs

Pour terminer ce cas d'étude et ce chapitre sur les relations, nous allons juste parler d'un cas qui restera ici *théorique* mais qui est très courant dans le monde du web et des bases de données.

On appelle cela "la relation avec propriété". Bon, c'est un peu long à écrire comme nom. Le mieux c'est de s'imaginer un système de vote "+1" réservé aux personnes qui ont un compte sur votre blog. (pour simplifier, on n'essaie pas de faire de -1)

Une personne peut voter pour plusieurs articles, et chaque article peut avoir un nombre important de vote. Mais en plus, nous, gérant du blog, on veut savoir si les gens votent même quand l'article a été posté il y a longtemps. Dans ce cas, il faut qu'on retienne la date du vote. Eh bien, c'est exactement là que vient la "relation avec propriété" : nous avons une relation n-n entre les utilisateurs et les articles, mais il faut aussi qu'on retienne la date.

Et là, il vous faudra vous souvenir de ce qu'il s'était passé au sein de la BDD quand on avait créé une relation n-n : une table intermédiaire avait été créée.

Eh bien nous allons devoir faire la même chose : nous allons créer une *entité intermédiaire* qui aura une relation 1-n avec les articles et une relation 1-n avec les utilisateurs.
De plus, pour s'assurer qu'on ne peut voter qu'une fois à un article, il faudra configurer un peu notre entité.

Je vous poste le code, il constitue un modèle pour vos futurs besoins :

```csharp

public class MemberComment
{
    [Key, Column(Order = 0)]
    public int MemberID { get; set; }
    [Key, Column(Order = 1)]
    public int VotedArticleID { get; set; }

    //les deux attributs virtuels suivants vous permettent d'utiliser les propriétés comme d'habitude
    //elles seront automatiquement liées à MemberID et VotedArticleID
    public virtual Member Member { get; set; }
    public virtual Article VotedArticle { get; set; }

    public DateTime VoteDate { get; set; }

}
```
Code: La classe de vote
