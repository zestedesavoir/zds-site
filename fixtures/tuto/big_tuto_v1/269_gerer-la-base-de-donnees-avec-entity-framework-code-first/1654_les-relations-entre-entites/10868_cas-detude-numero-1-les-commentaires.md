# Relation 1->n

Commençons à étoffer notre blog. Le principe d'un tel site est que chacun puisse commenter un article.

Pour simplifier, nous allons dire qu'un commentaire peut être publié par n'importe qui du moment que cette personne donne son adresse e-mail.

Ainsi, une représentation basique, comme nous l'avions fait jusqu'à présent du commentaire serait celle-ci :

```csharp
public class Commentaire{

    public int ID {get; set;}
    [DataType(DataType.Email)]
    public string Email {get; set;}
    [StringLength(75)]
    public string Pseudo {get; set;}
    [DataType(DataType.MultilineText)]
    public string Contenu {get; set;}
    public DateTime Publication{get; set;}
}
```
Code: Un commentaire basique

Le seul problème de cette représentation c'est qu'elle ne prend pas en compte le fait que le commentaire se réfère à un article. Je dirais même plus, le commentaire se réfère à un et un seul article.

Pour schématiser cela, on pourrait écrire :

![Relation 1-n non inversée](/media/galleries/304/36a78c61-5aba-47b0-9fa2-610ab519b80b.png.960x960_q85.jpg)

Ce schéma, signifie qu'il y a un lien entre le commentaire et l'article et donc qu'à partir d'un commentaire on peut retrouver l'article auquel il est lié.

Sous forme de code, cela s'écrit :

```csharp
public class Commentaire{

    public int ID {get; set;}
    [DataType(DataType.EmailAddress)]
    public string Email {get; set;}
    [StringLength(75)]
    public string Pseudo {get; set;}
    [DataType(DataType.MultilineText)]
    public string Contenu {get; set;}
    public DateTime Publication{get; set;}
    //On crée un lien avec l'article
    public Article Parent {get; set;}
}
```
Code: Relation 1-n

Jusque là rien de très compliqué.

[[i]]
|N'oubliez pas de créer un DbSet nommé Commentaires dans votre contexte

Pour créer un commentaire, le code ne change pas, il faudra juste s'assurer que lorsque vous créez le commentaire vous lui liez un article, sinon EntityFramework vous dira que la sauvegarde est impossible.

Là où le code va changer, c'est quand il va falloir aller chercher l'article lié au commentaire.

Par défaut, EntityFramework ne va pas le chercher par peur de surcharger la mémoire. Il faudra donc lui dire *explicitement* d'aller chercher l'objet.

Pour cela, il faut utiliser la méthode `Include`.

Cette méthode attend en paramètre le nom du lien à charger. Dans notre cas c'est `Parent`.

```csharp
//obtient le premier commentaire (ou null s'il n'existe pas) du premier article du blog
Commentaire com = bdd.Commentaires.Include('Parent').Where(c => c.Id = 1).FirstOrDefault();
Article articleLie = com.Article;//
```
Code: Trouver l'article lié

[[q]]
|J'ai un problème : ce que je veux, moi, c'est afficher un article grâce à son identifiant puis, en dessous afficher les commentaires liés.

Comme je te comprends ;). Pour faire cela, on dit qu'il faut "inverser" la relation 1-n.

# Inverser la relation 1-n

## Le principe

Derrière le mot "inverser", rien de très inquiétant finalement. Vous vous souvenez du schéma de tout à l'heure? Nous avions une flèche. Cette flèche disait dans quel sens on pouvait parcourir la relation. Comme nous voulons la parcourir dans le sens *inverse*, il faudra "implémenter" non plus une flèche simple mais une flèche double.

![Relation 1-n inversée](/media/galleries/304/e846acd6-7d9c-4d17-969a-d453776bc04f.png.960x960_q85.jpg)

A priori, cela ne devrait pas être trop compliqué de mettre en place cette inversion. En effet, si nous voulons une **liste** de commentaires, intuitivement, nous sommes tentés de mettre dans la classe Article un attribut de type `List<Commentaire>`:

```chsarp
public class Article{
    public List<Commentaire> Commentaires { get; set; }
}
```
Code: Inversion de la relation.

Sachez qu'on peut s'en contenter, néanmoins, cela peut poser quelques difficultés lorsque nous coderons par la suite.

## Lazy Loading

Souvenons-nous que nous utilisons un ORM : Entity Framework.

Ce qui est bien avec les ORM, c'est qu'ils créent leurs requêtes tous seuls.

A priori, néanmoins, il ne va pas charger tout seul les entités liées. Il vous faudra -comme lorsqu'on n'avait pas encore inversé la relation-, utiliser `Include` pour aller chercher la liste des commentaires.

Cela peut être intéressant de faire ça si vous devez précharger en une seule requête un nombre important de données.

Par contre, si vous ne devez en charger qu'une toute petite partie (pagination, objets les plus récents...) vous allez occuper de l'espace mémoire en préchargeant tout. Une astuce sera donc de charger uniquement *à la demande*. Dans le monde des ORMs, cette technique a un nom : le **lazy loading**.

[[i]]
|Le lazy loading est une fonctionnalité très appréciable des ORM, néanmoins, n'en abusez pas, si vous l'utilisez pour des gros volumes de données, votre page sera très longue à charger.

Pour activer le lazy loading, il faut ajouter le mot clef `virtual` devant notre liste de commentaires.

[[q]]
|Virtual? comme pour surcharger les méthodes héritées?

Oui, le même virtual. Mais à contexte différent, sens différent, vous vous en doutez.

```csharp
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
    }
```
Code: La classe Article complète

# Interface graphique : les vues partielles

Maintenant que vous avez mis à jour votre modèle, mis à jour votre contrôleur d'article, il faut qu'on affiche les commentaires.

Habituellement, les commentaires sont affichés dans la page `Details` de l'article.

Par contre, nous pouvons imaginer qu'ils seront affichés autre part : modération des commentaires, commentaire le plus récent en page d'accueil...

Mettre en dur l'affichage des commentaires dans la page d'article, ça peut être assez contre productif.

## Etape 1 : la liste des commentaires

Dans le dossier View, ajouter un dossier `Commentaire`. Puis ajoutez une vue nommée _List avec pour modèle `Commentaire`. Par contre, veillez à sélectionner "créer en tant que vue partielle" :

![Ajouter une vue partielle](/media/galleries/304/0026e111-a186-450e-8bbe-1e81a4ba6f08.png.960x960_q85.png)

[[i]]
|Vous remarquerez l'underscore utilisé dans le nom de la vue. C'est une convention pour les vues partielles.
