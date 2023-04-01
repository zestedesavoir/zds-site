## Définition

**Application sur une seule page**, cela peut sembler étrange à première vue.
Alors, qu'est-ce que c'est ? Une application sur une seule page est... une application Web qui ne charge qu'une seule et unique page HTML.

[[question]]
| Donc on est obligé de tout mettre dans un fichier?

Non, rassurez-vous. En fait, cela vaut juste dire que le serveur ne génèrera qu'une seule page html, pour le reste, il va être un peu plus fin.
Dans une application sur une seule page, le contenu se rafraîchit  de manière "dynamique" au fur et à mesure de l'interaction avec le visiteur. Par exemple, si vous faites un blog sur une seule page, lorsque l'utilisateur cliquera sur "commenter", le formulaire se créera tout seul et quand vous enverrez le commentaire, il ne rechargera pas la page, il va juste dire au serveur "enregistre le commentaire" et c'est tout.

Ce modèle utilise massivement des technologies JavaScript pour créer des applications Web fluides et réactives qui n'ont pas besoin de recharger constamment les pages.

## différence avec une application Web ASP.NET classique

Comme vous pouvez vous en douter, une application sur une seule page ne fonctionne pas de la même façon qu'une application Web classique. Dans une application Web classique, chaque fois que le serveur est appelé, il rend une nouvelle page HTML. Cela déclenche une actualisation de la page dans le navigateur.

Tandis qu'avec une application sur une seule page, une fois la première page chargée, toute interaction avec le serveur se déroule à l'aide d'appels JavaScript.

Un schéma vaut mieux qu'un long discours :

![Différence entre application classique et application sur une seule page](http://zestedesavoir.com/media/galleries/304/89acba7d-1851-4004-bb13-4b7e7b24aff2.png)

## avantages et inconvénients

Un avantage indéniable d'une application sur une seule page est la fluidité ; en effet les pages n'ont plus besoin d'être chargées, toute interaction avec l'interface utilisateur se produit côté client, par l'intermédiaire de JavaScript et CSS.

L'inconvénient est que la grosse partie de l'application se déroule côté client et non côté serveur : ce qui signifie pour un développeur ASP.NET d'utiliser plus de JavaScript que de C#.
