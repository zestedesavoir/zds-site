Doucement, la fin de la troisième partie de ce tutoriel approche, et avec elle vous avez appris les bases nécessaires pour créer un site web dynamique avec ASP.NET.

Avant de publier ce site web, vous allez néanmoins vouloir vous assurer que votre site fonctionne et que tout s'affiche là où il faut. Pour vous faciliter la tâche, vous allez sûrement ajouter quelques données à votre base de données.

Heureusement, comme nous avons choisi l'approche CodeFirst, il y a une méthode *simple* pour insérer des données **automatiquement** et ça, ça n'a pas de prix.

# Un jeu de données simple

Si vous vous souvenez de la vidéo sur les migrations, vous vous souviendrez que j'ai évoqué le fichier `Configuration.cs` du dossier `Migrations`. Dans ce fichier, se trouve une méthode `Seed`.

Sans tenter de traduction hasardeuse, le but de cette méthode est simple : ajouter des données à votre base de données pour que vous puissiez démarrer votre application.

Vous trouverez en argument de cette fonction le contexte de données qui établie la connexion avec votre BDD, profitons-en.

## Ajoutons un article

Commençons par faire simple. Ajoutons un article.

Cela se passe exactement comme dans nos contrôleurs. Il suffit de créer un objet `Article`, de l'ajouter au contexte et de sauvegarder le tout.

```csharp
context.Articles.Add(new Article
{
    Contenu = "plop !",
    Pseudo = "un pseudo",
    Titre = "mon titre",
});

context.SaveChanges();
```
Code: la Seed a un article !

Maintenant, dans l'hôte Powershell du gestionnaire de package, lancez `Update-Database`.

Et quand on regardera dans l'explorateur de serveur, notre nouvel article sera créé !

![Résultat de seed](http://zestedesavoir.com/media/galleries/304/e95ae0ae-28d7-40d1-a88a-dddb084cc143.png.960x960_q85.png)

Tant que nous sommes dans le fichier de migration, nous avons accès à des *méthodes d'extension* spécialement réalisées pour être utilisées dans la méthode Seed. L'un des cas est la méthode AddOrUpdate qui vient se greffer aux `DbSet` et qui vous permet d'ajouter une entité uniquement si elle n'est pas existante (i.e si aucun champ dont la valeur doit être unique possède déjà un doublon en base de données) et de la mettre à jour dans le cas contraire.

Dans le cadre d'une base de données de test, je préfère ne pas l'utiliser, mais quand on parlera des données pour le site final, ça peut **beaucoup** aider.

## Créons un compte administrateur

[[q]]
| Créer un compte utilisateur, c'est si différent que ça de créer un article?

En fait, si vous jetez un coup d'oeil au fichier `AccountController.cs`, vous vous rendrez compte que pour gérer la sécurité, ASP.NET MVC sépare pas mal les classes et au finale créer un compte utilisateur demande quelques prérequis. Or, comme nous n'avons pas vu en détail l'authentification dans notre blog, je préfère vous fournir quelques explications basiques ainsi que le code.

Un utilisateur, de base dans ASP.NET, est composé de deux entités distinctes :

- la première gère son **Identité** et son **Authenticité**
- la seconde gère ses **informations complémentaires**.

L'identité et l'authenticité sont deux concepts importants qui seront détaillés plus tard, mais pour faire simple, vous êtes identifiés lorsque vous avez donné votre pseudo, et authentifié quand vous avez donné le mot de passe adéquat.

Il faut ajouter que les utilisateurs ont des *roles*. Par exemple, sur zeste de savoir, je suis un simple membre, mais certains sont membre du *staff* et peuvent valider un tuto ou modérer les forums, et au dessus de tous, il y a des administrateurs qui ont sûrement quelques super pouvoirs.

Pour gérer tout ça, vous ne pourrez pas vous contenter de faire un `Context.Users.Add()`, vous le comprenez sûrement. Il faut appeler un *manager* qui lui même sait gérer les différentes tables qui lui sont présentés dans un *Store*.

Nous n'irons pas plus loin pour l'instant, passons au code :

```csharp
if (!context.Roles.Any(r => r.Name == "Administrator"))
{
    RoleStore<IdentityRole> roleStore = new RoleStore<IdentityRole>(context);
    RoleManager<IdentityRole> manager = new RoleManager<IdentityRole>(roleStore);
    IdentityRole role = new IdentityRole { Name = "Administrator" };

    manager.Create(role);
}

if (!context.Users.Any(u => u.UserName == "Proprio"))
{
    UserStore<ApplicationUser> userStore = new UserStore<ApplicationUser>(context);
    UserManager<ApplicationUser> manager = new UserManager<ApplicationUser>(userStore);
    ApplicationUser user = new ApplicationUser { UserName = "Proprio" };

    manager.Create(user, "ProprioPwd!");
    manager.AddToRole(user.Id, "Administrator");
}
```
Code: la création du compte administrateur

# Un jeu de données complexe sans tout taper à la main

Nous l'avons vu, pour créer un jeu de données, il suffit de créer des objets et de les ajouter à la base de données. Seulement la méthode utilisée jusque là est un peu embêtante :

- pour créer un jeu de données qui doit être représentatif de tous les cas d'utilisation, il faut tout écrire à la main. Imaginez-vous devoir écrire 50 articles complets juste pour tester !
- Vous perdez le "sens" de vos données. Si pour être représentatif, vous devez avoir un article qui a un tag, un qui en a deux, un qui n'en a pas, répété cela pour les articles qui sont courts, longs, très longs... Si vous chargez vos articles dans un fichier json comme je vous l'avez proposé dans la partie précédente, comment savez vous quel article représente quel cas quand vous lisez votre code? Comment savez-vous que vous n'avez pas oublié de cas?

Pour résoudre ces problèmes, nous allons donc procéder par étapes:

Premièrement, nous allons générer des données **cohérentes** en grand nombre de manière automatique.

Pour cela, téléchargez le package NuGet `Faker.NET`. Ce module vous permet de générer automatiquement plein de données. Vous aurez droit à :

Nom | Commentaires | Méthodes utiles (non exhaustif)
----|--------------|--------------------------------
Address|Vous permet d'accéder à tout ce qui concerne une adresse, de la rue au code postal.|City(), StreetAddress(). Beaucoup de méthodes propres aux US et UK.
Company|Vous permet d'accéder aux différentes dénominations pour les entreprises|Name() (pour le nom) et CatchPhrase() (pour simuler un slogan)
Internet|Très utile pour simuler ce qui est propre aux sites web| DomainName() et DomainSuffix() pour générer des adresses de site web, UserName() pour générer un pseudo !
Lorem|Génère des textes plus ou moins long sur le modèle du [Lorem](http://fr.lipsum.com/).|Sentence() pour générer une phrase, `Words(1).First()` pour un seul mot, Paragraph() pour un seul paragraphe, Paragraphs(42) pour avoir la réponse à la question sur l'univers et le sens de la vie en latin, of course.
Name|Tout ce qui concerne l'état civil d'une personne | First() (prénom) Last() (nom de famille)
Phone|génère des numéros de téléphone|Number(), il n'y a que ça
RandomNumber|Equivalent à la méthode Next() de l'objet Random|...

Ainsi pour créer un article avec deux tags, nous pourrons faire :

```csharp
Tag tag1 = new Tag { Name = Faker.Lorem.Words(1).First() };
Tag tag2 = new Tag { Name = Faker.Lorem.Words(1).First() };
context.Tags.AddOrUpdate(tag1, tag2);
Article article = new Article
    {
        Contenu = Faker.Lorem.Paragraphs(4),
        Pseudo = Faker.Internet.UserName(),
        Titre = Faker.Lorem.Sentence(),
        Tags = new List<Tag>()
    };
article.Tags.Add(tag1);
article.Tags.Add(tag2);
context.Articles.Add(article);
```
Code: Débutons avec Faker

# Un jeu de données pour le debug et un jeu pour le site final

Je vous propose de terminer cette partie sur les jeux de données par la création de deux jeux de données : un pour les tests et un pour la production.

En effet, les caractéristiques de ces jeux de données et la manière de les créer est différente en fonction du contexte. Regardons un peu ce que nous attendons de ces deux jeux de données :

**Le jeu de tests** doit :

- Permettre de tester *tous* les cas, du plus courant au plus étrange;
- Représenter une utilisation *fidèle* du site, lorsque je teste mon blog, je ne vais pas tenter d'y mettre 15 000 articles si je sais que je ne vais en poster qu'un par mois (soit 24 en deux ans), à l'opposé, si je m'appelle zeste de savoir, je dois pouvoir obtenir une dizaines de tutoriels longs avec beaucoup de contenu pour voir comment ça fonctionne.

** Le jeu de production ** doit :

- Permettre l'installation du site;
- Etre prévisible et donc *documenté*, si vous créez un compte administrateur (obligatoire), il doit avoir un mot de passe par défaut qu'on peut trouver facilement;
- Ne pas casser les données déjà présente en production.

Je vais donc vous donner quelques conseils pour que vous mettiez en place des données cohérentes rapidement.

Nous allons nous servir d'une propriété très intéressante des fichiers de configuration de ASP.NET. Comme nous avons plusieurs "versions de données", nous allons aller dans le fichier `Web.config`.

Une fois dans ce fichier, il faudra localiser la section `appSettings`. Là, nous y ajouterons une ligne `<add key="data_version" value="debug"/>`.

Cela dit que la "version des données" par défaut sera "debug". Vous pourrez changer ça, mais cela n'aura pas d'importance puisque de toute façon nous allons dire explicitement quelles données utiliser quand on fait des tests et quand on met en production.

## Pour les données de tests :

1. Allez dans le fichier Web.Debug.Config, et ajoutez-y le code suivant
```xml
<appSettings>
  <add xdt:Transform="Replace" xdt:Locator="Match(key)" key="data_version" value="debug"/>
</appSettings>
```
Cela aura pour effet de dire "quand tu buildes en debug, trouve-moi la propriété "data_version" et remplace sa valeur par "debug".

2. Dans le fichier `Migrations/Configuration.cs`, créez une méthode privée nommée `seedDebug` qui a les mêmes arguments que `Seed` et coupez-collez le code de la méthode Seed dans `seedDebug`.
3. Dans la méthode Seed, vous allez maintenant préciser "si je veux des données de debug, alors, appeler `seedDebug`.
```csharp
protected override void Seed(Blog.Models.ApplicationDbContext context)
{
    if (ConfigurationManager.AppSettings["data_version"] == "debug")
    {
         seedDebug(context);
    }
}
```

Vous pouvez étoffer votre code de test en y mettant de nouvelles données, vous pouvez aussi vous inspirer du patron de conception Factory pour créer des articles qui correspondent à des paramètres différents.

## Pour le jeu de données de production

Tout comme précédemment, nous allons utiliser la transformation des fichiers de configuration.

Nous allons donc aller dans le fichier Web.Release.config et y entrer le code :

```xml
<appSettings>
  <add xdt:Transform="Replace" xdt:Locator="Match(key)" key="data_version" value="production"/>
</appSettings>
```

Du coup on peut encore créer une méthode privée dans le fichier `Migrations/Configuration.cs` et l'appeler de manière adéquate :

```csharp
        protected override void Seed(Blog.Models.ApplicationDbContext context)
        {
            if (ConfigurationManager.AppSettings["data_version"] == "debug")
            {
                seedDebug(context);
            }
            else if (ConfigurationManager.AppSettings["data_version"] == "production")
            {
                seedProduction(context);
            }

        }
        private void seedProduction(ApplicationDbContext context)
        {

        }
```

Il ne nous reste plus qu'à savoir quoi mettre dans la fonction `seedProduction`.

Et là, plus question de faire de la génération automatique, il va falloir créer les objets un à un.

Dans cette configuration, j'ai un petit faible pour les fichiers *JSON* ou *YAML* qui regroupent une description des objets à créer. On appelle ces fichiers des *fixtures*.

Ils ont de nombreux avantages :

- Ils sont plus lisibles que du code;
- Ils sont facilement modulables (ajouter ou retirer un objet est très facile);
- Ils sont **versionables**, c'est à dire que si vous travailler à plusieurs avec des outils comme GIT ou SVN, ces fichiers seront correctement gérés par ces outils.

Surtout, cette fonction ne **doit pas** détruire les objets déjà présent. Vous allez donc devoir *absolument* utiliser la méthode `AddOrUpdate` et faire les vérifications d'existence quand le cas se présente.
