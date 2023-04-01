Jusqu'à maintenant, nous avons décrit la technologie ASP.NET comme un **ensemble d’outils**. Il n’y a rien de faux dedans, mais en informatique nous préférons employer le terme **framework**.
Un framework est très utilisé dans le domaine de la programmation et nous allons voir pourquoi.

[[question]]
| Qu’est-ce que ça va m’apporter d’utiliser un framework ?

Tout d’abord, décortiquons le mot : framework vient de l'anglais et se traduit littéralement par « **cadre de travail** ». Pour simplifier la chose, nous pouvons dire qu’un framework est une grosse boîte à fonctionnalités et de règles de codage qui va nous permettre de réaliser nos applications informatiques.
Il est entre autres destiné au développement d’une application Web, ce qui nous intéresse.

Lors du développement d’une application (Web ou autre) le développeur utilise un langage de programmation, prenons le **C#**.
Afin d’être efficace et éviter de se casser la tête à sans cesse repartir de zéro, le langage de programmation est accompagné d'un framework :

Celui-ci contient des espaces de noms, des classes, des méthodes, des structures et d’autres outils que le développeur peut utiliser en relation ici avec le C#.
Il s'occupe de la forme et permet au développeur de se concentrer sur le fond.

La taille d’un Framework comme ASP.NET est telle qu’il est impossible pour nous de tout connaître, c’est pour cette raison qu’il existe une documentation associée afin de s’y retrouver.
Utilisez la documentation le plus souvent possible !
Nous ne vous le rappellerons jamais assez.
De plus ASP.NET et C# possède une documentation commune extrêmement bien structurée que vous découvrirez tout au long de ce tutoriel.

[[information]]
| Cette documentation s'appelle la **MSDN Library**. Elle est accessible en **français** via ce lien : [MSDN Library](http://msdn.microsoft.com/fr-fr/library/ms123401.aspx). Cet acronyme se traduira par "Réseau des Développeurs Microsoft" car il concentre l'essentiel des technologies de développement de l'entreprise.

## Framework et développement

Après avoir introduit la notion de framework, nous allons exposer les avantages de l'utilisation d'un framework au sein d'une application Web.

Nous pouvons commencer par énumérer la **rapidité** : le Framework est un ensemble de briques qui nous évite à réinventer la roue.
En effet, ces briques sont développées par des équipes de développeurs à plein temps, elles sont donc très flexibles et très robustes.
Vous économisez ainsi des heures de développement !
Par exemple, un Framework peut proposer des composants graphiques avec des propriétés toutes prêtes sans que vous ayez à tout refaire vous même.

L'**organisation** du développement de l'application : utiliser un Framework demande de respecter l'architecture de celui-ci.
Une bonne utilisation de la documentation et le respect des règles du code permettent de créer une application maintenable par la suite.
D'une autre part, le Framework ASP.NET nous permet de nous baser sur plusieurs *architectures* différentes.
Ce cours traitera de **MVC** ; nous verrons cela bientôt, mais sachez pour le moment que c'est une façon d'organiser son code pour séparer la partie interface graphique (HTML) de la partie logique (C#).

Utiliser un Framework facilite le **travail en équipe** : du fait des conventions et des pratiques de code.
La connaissance d'un Framework vous permettra de vous intégrer rapidement dans des projets l'utilisant sans avoir besoin de formation.

Et enfin un point très important : l'esprit **communautaire**.
Un Framework se base sur une grosse communauté de développeurs.
Elle fournit toutes les ressources nécessaires afin d'éviter de se perdre lors du développement d'une application.
Citons comme exemple la documentation (MSDN) ou encore ce tutoriel sur l'ASP.NET.
De plus, nous n'avons pas à nous soucier des bugs internes au Framework, nous ne sommes qu'*utilisateurs* de celui-ci.
Les développeurs travaillant sur le Framework sont suffisamment chevronnées pour régler les problèmes rapidement, donc il y a une **sécurité** supplémentaire.
Et pour renforcer l'esprit communautaire, toute la pile technologique autour de ASP.NET MVC est [open source](http://aspnetwebstack.codeplex.com/)!


Pour résumer les avantages d'un Framework :

- rapidité : nous utilisons des briques toutes prêtes.
- organisation du code : production d'un code structuré et maintenable.
- connaissances communes : le travail est basé sur une seule et même boîte à fonctionnalités.
- communauté : l'aide et les ressources de qualité ne manquent pas.
- maintenance : en tant qu'utilisateurs, nous ne nous occupons que du fond de notre application, la forme est gérée par le Framework lui-même.
- sécurité : les développeurs et la communauté s'occuperont de corriger un bug, et vous n'aurez plus qu'à suivre les mises à jour.

[[question]]
| Et il n'y a pas d'inconvénients dans tout cela ?

A vrai dire, nous n'en voyons pas mis à part le fait que pour utiliser un Framework, il y a un temps d'apprentissage plus ou moins long. Utiliser un Framework s'apprend en plus de la programmation.

Mais à choisir, mieux vaut perdre un peu de temps pour apprendre à utiliser un Framework afin de gagner du temps de développement et de maintenance pour vos applications Web par la suite.

## Un exemple concret : le Framework .NET

Pour suivre ce tutoriel, nous vous avons conseillé d'avoir quelques notions de **C#** (ou de VB.NET). Ces deux langages reposent sur un Framework : le **Framework .NET** (prononcé *dot net*). Vous l'avez quasiment tout le temps utilisé, peut-être sans vous en rendre compte.

Pour illustrer cela, regardez bien ces deux bouts de code :

```csharp
using System;

class Program
{
    static void Main(String[] args)
    {
        String message = "Bonjour";
        Console.WriteLine(message);
    }
}
```

```vbnet
Imports System;

Public Module Coucou
    Public Sub Main()
        Dim message As String = "Bonjour"
        Console.WriteLine(message);
    End Sub
End Module
```

Le deux codes font la même action: afficher un message à l'écran. Malgré la différence entre les deux langages, nous retrouvons des éléments en commun :

- utilisation de la même bibliothèque `System` ;
- la classe `Console` ;
- la méthode `WriteLine` qui permet d'écrire à l'écran.

Dans les deux cas, nous ne faisons qu'utiliser des éléments appartenant au Framework .NET.

C’est tout ce qu’il y a à savoir pour l’instant, nous reviendrons un peu plus en détail sur le .NET dans les chapitres suivants. Pour l’heure, il est important de retenir que c’est grâce au langage de programmation C# mêlés aux composants du Framework .NET et bien sûr à **ASP.NET** que nous allons pouvoir développer des applications pour le Web.
