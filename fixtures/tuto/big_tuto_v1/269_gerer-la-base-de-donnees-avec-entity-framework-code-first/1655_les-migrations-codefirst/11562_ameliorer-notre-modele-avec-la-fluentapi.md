[[a]]
|Les explications qui vont suivre s'adressent surtout aux personnes qui ont une bonne connaissance des bases de données.
|Nous l'avons mis dans ce tutoriel car vous trouverez rapidement des cas où il faut en passer par là, mais ils ne seront pas votre quotidien, rassurez-vous.

Si vous vous souvenez de l'introduction à l'approche *Code First*, je vous avais parlé de trois outils dont un qui s'appelle la *Fluent API*.

Cette API est très complète et permet en fait de personnaliser d'une manière encore plus complète vos entités quand bien même aucune Annotation n'existe.

Elle est complétée par la possibilité de personnaliser un maximum les migrations qui, je vous le rappelle, sont des simple fichiers de code.

Ce chapitre pourrait mériter un livre complet qui s'appellerait alors "améliorer les performances, la sécurité et l'utilisation de votre base de données". J'ai pour ma part choisi deux "cas d'étude" que j'ai rencontré dans plusieurs de mes projets, et pour le premier, il a même été **tout le temps rencontré**.

Nous allons donc conjuguer la `Fluent API` avec une possible connaissance du SQL pour des cas très précis tels que l'ajout de contrainte plus complexes ou l'utilisation de fonctionnalités avancées des bases de données.

# Quand les relations ne peuvent être pleinement décrites par les annotations

Lors que vous définissez une relation, parfois, elle est plus complexe qu'il n'y parait et les annotations ne suffisent pas à la décrire proprement ou alors il faut se torturer un peu l'esprit pour y arriver.

C'est à ce moment là qu'intervient la Fluent API. Je vais vous présenter deux cas "typiques" qui vous demanderont d'utiliser la FluentAPI.

Le premier cas, on peut le représenter très simplement sous la forme d'un schéma :

![Cycle de relation](http://zestedesavoir.com/media/galleries/304/2a5da711-aaf9-4d20-a0f5-7348bd879132.png.960x960_q85.jpg)

Nous avons donc à un moment dans notre modèle, une entité C qui est liée fortement à une instance d'une entité B qui est liée à une instance d'une entité A qui est liée à une instance d'une entité C.

Sauf qu'il est tout à fait possible que l'instance C de départ et celle d'arrivée soient... une seule et unique instance. Si vous pensez que ça n'arrive pas dans votre cas précis, souvenez vous de la loi de Murphy "S'il existe une manière pour que l'action en cours se terminent par une catastrophe, alors, ça finira par arriver".

Maintenant, imaginez vous, que vous avez besoin de supprimer l'entité A.

Par défaut, ce genre de relation entraine une suppression en cascade. Donc quand entity framework enverra la commande SQL associée à la suppression de A, C va être détruite. Mais du coup, B aussi. Et du coup A aussi, et du coup... attendez, on a déjà supprimé A? Donc, quand on a demandé la suppression de C, la base de donnée n'était plus cohérente. Donc, on ne peut pas appliquer "supprimer C", comme "supprimer C" a été demandé par "supprimer B", on ne peut pas non plus demander "supprimer B" ni "supprimer A".

Plus globalement, cette situation peut arriver selon deux schéma : le cycle (cercle) et le diamant (losange). Il faudra donc décrire ce qu'il faut faire pour briser cette figure.

![Relation en losange](http://zestedesavoir.com/media/galleries/304/1638bc6d-c528-4306-ba96-4ddc8767d725.png.960x960_q85.jpg)

La solution la plus simple est de décider une entité dont la suppression n'engendrera pas de suppression en cascade. Le problème c'est que cela génèrera la possibilité que l'entité liée ne soit liée à rien. Il faudra donc dire que la relation est "optionnelle".

Pour cela, il faudra aller dans le fichier qui contient notre contexte de données. Nous allons y surcharger la méthode `OnModelCreating`, comme ceci :

```csharp
public class ApplicationDbContext : IdentityDbContext<ApplicationUser>
{
        public ApplicationDbContext()
            : base("DefaultConnection", throwIfV1Schema: false)
        {

        }
        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);
        }
}
```
Code: Surcharge de la méthode OnModelCreating

A l'intérieur de cette méthode, nous allons utiliser les possibilités du [DbModelBuilder](https://msdn.microsoft.com/fr-fr/library/system.data.entity.dbmodelbuilder%28v=vs.113%29.aspx).

Puis nous allons décrire pas à pas comment doivent se comporter nos entités. Dans le cas des A/B/C, par exemple, nous aurions pu écrire :

```csharp

modelBuidler.Entity<A>()
            .HasMany(obj => obj.BProperty)
            .WithOptional(objB -> objB.AProperty)
            .WillCascadeOnDelete(false);// on dit explicitement qu'il n'y a pas de suppression en cascade
```

Lorsque vous recréerez une migration, le code de génération de la base de données sera amendé avec cette gestion des conflits.
