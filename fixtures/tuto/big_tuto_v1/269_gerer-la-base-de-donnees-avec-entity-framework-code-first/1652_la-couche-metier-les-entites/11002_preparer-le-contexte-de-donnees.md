Nous allons vouloir *enregistrer* nos données dans la base de données. En génie logiciel on dit souvent que l'on assure la **persistance** des données. Comme dans les jeux en lignes *à monde persistant* en somme.

Lorsque vous utilisez EntityFramework, le lien fait entre la base de données et votre application se situe au niveau d'un objet appelé `DbContext`.

Si vous visitez un peu les classes que Visual Studio vous a générées, vous ne trouvez aucune classe appelée `DbContext`. Par contre vous trouvez une classe nommée `ApplicationDbContext` qui hérite de `IdentityDbContext`.

```csharp


    public class ApplicationDbContext : IdentityDbContext<ApplicationUser>
    {
        public ApplicationDbContext()
            : base("DefaultConnection", throwIfV1Schema: false)
        {
        }

        public static ApplicationDbContext Create()
        {
            return new ApplicationDbContext();
        }
    }

```
Code: ApplicationDbContext

En fait, comme nous avons créé une application web avec authentification, VisualStudio a préparé un contexte de données qui pré-enregistre **déjà** des classes pour :

- les utilisateurs
- leur informations personnelles (customisable)
- leur rôle dans le site (Auteur, Visiteur, Administrateur...)
- les liens éventuels avec les sites comme Facebook, Twitter, Google, Live...

`IdentityDbContext` est donc un `DbContext`, c'est là que la suite se passera.

# Prendre le contrôle de la base de données

Avant toute chose, comme nous somme en plein développement nous allons faire pleins de tests. Ce qui signifie que nous allons vouloir souvent changer la structure du modèle.

Nous verrons plus tard qu'il existe un outil très puissant pour permettre de mettre à jour une base de données qu'on appelle les *migrations*. Pour simplifier les choses, nous ne les mettrons en place qu'un peu plus tard.

Pour l'instant, il faudra que nous supprimions puis recréions la base de données à chaque changement.

Pour cela, regardez le dosser `App_Data`. Cliquez droit, puis "Ajouter>nouvel élement".

![Nouvel Elément](/media/galleries/304/8f5127f8-8b22-4d05-bef1-5c21aa621195.png.960x960_q85.jpg)

Sélectionnez "Base de données SQL Serveur" (selon votre version de Visual Studio, il précisera ou pas (LocalDb)). Donnez lui le nom `sqldb`

![Créez la base de données](/media/galleries/304/4de83592-47cc-450f-9627-016823e57acd.png.960x960_q85.jpg)

Maintenant, allons à la racine du site et ouvrons le fichier Web.config. Trouvons la `connectionString` nommée `DefaultConnection` et changeons l'adresse de la base de données pour faire correspondre à `sqldb.mdf`.

```xml hlines="2"
<connectionStrings>
    <add name="DefaultConnection" connectionString="Data Source=(LocalDb)\v11.0;AttachDbFilename=|DataDirectory|\sqldb.mdf;Initial Catalog=aspnet-Blog-20141014093301;Integrated Security=True" providerName="System.Data.SqlClient" />
  </connectionStrings>
```
Code: Web.config, ConnectionString

# Persister une entité

Pour persister une entité, il n'y a qu'une seule ligne à ajouter à notre DbContext : `public DbSet<TEntity> Nom { get; set; }`.

Ce qui donne, dans le cas des articles :

```csharp hlines="7"
public class ApplicationDbContext : IdentityDbContext<ApplicationUser>
    {
        public ApplicationDbContext()
            : base("DefaultConnection", throwIfV1Schema: false)
        {
        }
        public DbSet<Article> Articles { get; set; }
        public static ApplicationDbContext Create()
        {
            return new ApplicationDbContext();
        }
    }
```
Code: Les articles seront persistés

Et cela sera comme ça pour **toutes** nos entités.

[[i]]
|Petite astuce appréciable : lorsque vous créez une nouvelle entité, ajoutez-la tout de suite au contexte. Une fois cela fait, vous aurez accès au scafolding complet pour les contrôleurs.
