Allons donc dans notre contrôleur `ArticleController.cs`.

La première étape sera d'ajouter une instance de notre contexte de donnée en tant qu'attribut du contrôleur.

```csharp

public class ArticleController{

    private ApplicationDbContext bdd = ApplicationDbContext.Create();//le lien vers la base de données
    /* reste du code*/
}
```
Code: Ajouter un lien vers la base de données

Une fois ce lien fait, nous allons nous rendre dans la méthode `List` et nous allons remplacer le vieux code par une requête à notre base de données.

```csharp
 try
{
   List<Article> liste = _repository.GetAllListArticle().ToList();
   return View(liste);
}
catch
{
    return View(new List<Article>());
}
```
Code: L'ancien code

Entity Framework use Linq To SQL pour fonctionner. Si vous avez déjà l'habitude de cette technologie, vous ne devriez pas être perdu.

Sinon, voici le topo :

Linq, pour *Language Integrated Query*, est un ensemble de bibliothèques d'extensions codées pour vous simplifier la vie lorsque vous devez manipuler des collections de données.

Ces collections de données peuvent être dans des tableaux, des listes, du XML, du JSON, ou bien une base de données !

Quoi qu'il arrive, les méthodes utilisées seront toujours les mêmes.

# Obtenir la liste complète

Il n'y a pas de code plus simple : `bdd.Articles.ToList();`. Et encore, le `ToList()` n'est nécessaire que si vous désirez que votre vue manipule une `List<Article>` au lieu d'un `IEnumerable<Article>`. La différence entre les deux : la liste est totalement chargée en mémoire alors que le `IEnumerable` ne fera en sorte de charger qu'un objet à la fois.

Certains cas sont plus pratiques avec une liste, donc pour rester le plus simple possible, gardons cette idée là !

# Obtenir une liste partielle (retour sur la pagination)

Souvenez-vous de l'ancien code :

```csharp
public ActionResult List(int page = 0)
        {
            try
            {
                List<Article> liste = _repository.GetListArticle(page * ARTICLEPERPAGE, ARTICLEPERPAGE).ToList();
                ViewBag.Page = page;
                return View(liste);
            }
            catch
            {
                return View(new List<Article>());
            }
        }
```
Code: La pagination dans l'ancienne version

Notre idée restera la même avec Linq. Par contre Linq ne donne pas une méthode qui fait tout à la fois.

Vous n'aurez droit qu'à deux méthodes :

- `Take` : permet de définir le nombre d'objet à prendre;
- `Skip` : permet de définir le saut à faire.

Néanmoins, avant toute chose, il faudra que vous indiquiez à EntityFramework comment ordonner les entités.

Pour s'assurer que notre liste est bien ordonnée par la date de publication (au cas où nous aurions des articles dont la publication ne s'est pas faite juste après l'écriture), il faudra utiliser la méthode `OrderBy`.

Cette dernière attend en argument une fonction qui retourne le paramètre utilisé pour ordonner.

Par exemple, pour nos articles, rangeons-les par ordre alphabétique de titre :

```csharp
bdd.Articles.OrderBy(a => a.Titre).ToList();
```
Code: La liste est ordonnée

Ainsi, avec la pagination, nous obtiendrons :

```csharp
public ActionResult List(int page = 0)
        {
            try
            {
                //on saute un certain nombre d'article et on en prend la quantité voulue
                List<Article> liste = bdd.Articles
                                         .OrderBy(a => a.ID)
                                         .Skip(page * ARTICLEPERPAGE)
                                         .Take(ARTICLEPERPAGE).ToList();
                ViewBag.Page = page;
                return View(liste);
            }
            catch
            {
                return View(new List<Article>());
            }
        }
```
Code: Nouvelle version de la pagination

Par exemple si nous avions 50 articles en base de données, avec 5 articles par page, nous afficherions à la page 4 les articles 21 22 23 24 25.

Mais le plus beau dans tout ça, c'est qu'on peut chaîner autant qu'on veut les Skip et les Take. Ainsi en faisant : `Skip(5).Take(10).Skip(1).Take(2)` nous aurions eu le résultat suivant :

->
N° article | Pris
-----------|-------
1|non
2|non
3|non
4|non
5|non
6|oui
7|oui
8|oui
9|oui
10|oui
11|oui
12|oui
13|oui
14|oui
15|oui
16|non
17|oui
18|oui
<-

[[a]]
|Si vous voulez que votre collection respecte un ordre spécial, il faudra lui préciser l'ordre **avant** de faire les `Skip` et `Take`, sinon le système ne sait pas comment faire.

# Filtrer une liste

## La méthode Where

Avant de filtrer notre liste, nous allons légèrement modifier notre entité `Article` et lui ajouter un paramètre booléen nommé `EstPublie`.
```csharp
     public class Article
    {
        public Article()
        {
            EstPublie = true;//donne une valeur par défaut
        }
        public int ID { get; set; }
        [Column("Title")]
        [StringLength(128)]
        public string Titre { get; set; }
        [Column("Content")]
        public string Texte { get; set; }
        public string ThumbnailPath { get; set; }
        public bool EstPublie { get; set; }
    }
```
Code: Ajout d'un attribut dans la classe Article

Maintenant, notre but sera de n'afficher que les articles qui sont marqués comme publiés.

Pour cela il faut utiliser la fonction `Where` qui prend en entrée un délégué qui a cette signature :

```csharp
delegate bool Where(TEntity entity)
```
Code: Signature de la méthode Where

Dans le cadre de notre liste, nous pourrions donc utiliser :

```csharp hl_lines="6"
public ActionResult List(int page = 0)
        {
            try
            {
                //on saute un certain nombre d'article et on en prend la quantité voulue
                List<Article> liste = bdd.Articles.Where(article => article.EstPublie)
                                         .Skip(page * ARTICLEPERPAGE).Take(ARTICLEPERPAGE).ToList();
                ViewBag.Page = page;
                return View(liste);
            }
            catch
            {
                return View(new List<Article>());
            }
        }
```
Code: Filtrage de la liste en fonction de l'état de l'article

[[a]]
|Dans vos filtres, toutes les fonctions ne sont pas utilisables dès qu'on traite les chaînes de caractères, les dates...

## Filtre à plusieurs conditions

Pour mettre plusieurs conditions, vous pouvez utiliser les mêmes règles que pour les embranchements `if` et `else if`, c'est à dire utiliser par exemple `article.EstPublie && article.Titre.Length < 100` ou bien `article.EstPublie || !string.IsNullOrEmpty(article.ThumbnailPath)`.

Néanmoins, dans une optique de lisibilité, vous pouvez remplacer le `&&` par une chaîne de `Where`.

```csharp
List<Article> liste = bdd.Articles.Where(article => article.EstPublie)
                                  .Where(article => !string.IsNullOrEmpty(article.ThumbnailPath)`
```
Code: Chaînage de Where
