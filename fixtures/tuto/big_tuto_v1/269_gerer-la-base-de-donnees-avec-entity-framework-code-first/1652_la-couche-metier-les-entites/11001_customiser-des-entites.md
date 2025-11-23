# Le comportement par défaut

Avant de *personnaliser* les entités, tentons de comprendre le comportement par défaut.

Premièrement, si votre entité est bien enregistrée, elle sera transformée en **table** SQL. Cette **table** portera le même nom que l'entité. Les colonnes prendront le nom de l'attribut qu'elles cartographient.

->
+----------------+------------------------+---------------------------------+-------------------------------+
|ID(int)         |Titre(Varchar128)       |Texte(Text)                      |ThumbnailPath                  |
+================+========================+=================================+===============================+
|1               |Premier article         |Bonjour à tous, bienvenu dans    |/images/coeur.png              |
|                |                        |mon blog !                       |                               |
+----------------+------------------------+---------------------------------+-------------------------------+
|2               |Billet d'humeur         |Je suis trop heureux d'avoir     |/images/content.png            |
|                |                        |créé mon blog !                  |                               |
+----------------+------------------------+---------------------------------+-------------------------------+
|...             |...                     |............................     |...................            |
+----------------+------------------------+---------------------------------+-------------------------------+
Table: La table SQL générée à partir de notre entité
<-

# Changer le nom des tables et colonnes

Dans certaines applications, les gens aiment bien faire en sorte que les tables aient un préfixe qui symbolisent leur application. Cela permet, par exemple, de mettre plusieurs applications dans une seule même base de données mais sans changer l'annuaire des membres.

Pour cela, il faudra expliquer à EntityFramework que vous désirez changer le nom de la table voire des colonnes grâce aux **[attributs](http://msdn.microsoft.com/fr-fr/data/jj193542.aspx)** `[Table("nom de la table")]` et `[Column("Nom de la colonne")]`.

```csharp
[Table("blog_Article")]
public class Article{
    public int ID {get; set;}
    [Column("Title")]
    [StringLength(128)]
    public string Titre{get; set;}
    [Column("Content")]
    public string Texte{get; set;}
    public string ThumbnailPath{get; set;}
}
```
Code: Personnalisation de la classe

# Les données générées par la base de données

La base de données peut calculer certaines valeurs pour vos entités.

Inconsciemment nous avons déjà mis en place cette fonctionnalité précédemment. Rappelez-vous, je vous ai dit qu'une entité avait besoin d'un attribut `ID`.

Cet attribut, par défaut est compris par le programme comme possédant les particularités suivantes :

- nom de colonne = `ID`
- entiers positifs
- valeurs générées par la base de données : de manière séquentielle et unique à chaque instance

Si nous devions coder cela nous mettrions :

```csharp
public class Article{
    [Column("ID")]
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.IDENTITY)]
    public int ID_That_Is_Not_Conventional{get; set;}
    [Column("Title")]
    [StringLength(128)]
    public string Titre{get; set;}
    [Column("Content")]
    public string Texte{get; set;}
    public string ThumbnailPath{get; set;}
}
```
Code: Génération de l'ID par la base de données
