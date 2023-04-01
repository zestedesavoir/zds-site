Lorsque nous créons une application web, nous devons répondre à un **besoin métier**.

Ce besoin vous permet de comprendre qu'il y a des structures de données qui sont courantes. C'est de là que naissent les **classes métier** aussi appelées "entités" dans notre cours.

Nous avons décidé que nous allions créer un *blog*. De manière basique, un blog se représente ainsi :

le contenu principal est appelé **article**.

Un article est composé de plusieurs choses :

- un titre
- un texte
- une thumbnail (ou imagette en français)

Les articles pourront être **commentés** par différentes personnes.

Un commentaire est composé de plusieurs choses :

- un titre
- un texte
- un renvoie vers le site web de l'auteur du commentaire

Et ainsi de suite.

Comme vous pouvez le constater, ces description amènent à une conclusion simple : les "entités" peuvent être représentées par de simples classes telles qu'on a l'habitude de manipuler.

Il y a cependant une nécessité qui est **imposée** par le fait qu'on va *persister* les objets : il faut qu'ils soient identifiables.

A priori, deux articles peuvent avoir le même titre, ce dernier n'est donc pas l'identifiant de l'article.

Le texte peut être très long, comparer deux textes pour trouver l'identifiant du site ne serait donc pas performant.

C'est pour cela que nous allons devoir créer un attribut spécial. Par *convention*, cet attribut s'appelle `ID` et est un entier.

Une version simplifiée (et donc incomplète) de notre classe `Article` serait donc :

```csharp
public class Article{ //important : la classe doit être publique

    public int ID {get; set;}
    public string Titre{get; set;}
    public string Texte{get; set;}
    public string ThumbnailPath{get; set;}

}
```
Code: Structure simplifiée de la classe `Article`

Vous pouvez le constater, notre classe est surtout composée de propriétés simples (int, string, float, decimal) publiques avec un accès en **lecture et en écriture**.

Vous pouvez aussi utiliser certains objets *communs* tels que :

- DateTime
- TimeSpan
- Byte[]

Vous trouverez un récapitulatif complet des types supportés de base sur [msdn](https://www.devart.com/dotconnect/db2/docs/DataTypeMapping.html).

[[a]]
| Cela signifie que les `struct` ne sont pas compatibles de base. N'utilisez que les objets simples ou les objets que vous avez vous-même créés.
