Un site internet est un point d'entrée important pour pas mal d'attaques.
Certaines de ces attaques sont brutales et pour vous protéger, vous aurez besoin d'une infrastructure importante qui est souvent la responsabilité de votre *hébergeur*.

D'autres, à l'opposé, sont plus pernicieuses car elles se servent de failles ouvertes au sein même de votre code.
Nous allons voir quelques-unes des failles les plus connues sur le web et surtout qu'ASP.NET vous aide énormément à vous en protéger.

## La faille CSRF

Pour vous souhaiter la bienvenue dans le vaste monde des failles de sécurité, voici votre premier acronyme CSRF pour **Cross Site Request Forgery*[^wiki_csrf].

Cette faille ne concerne que les formulaires de type POST. Elle se sert du fait que créer une requête http à partir de rien est très facile.

Surtout, elle s'aide beaucoup du *[social engineering](https://www.securiteinfo.com/attaques/divers/social.shtml)* et du réflex pavlovien des gens qui consiste à cliquer sur tous les liens qu'ils voient.

Cette attaque consiste à usurper l'identité d'un membre qui a le droit de gérer le contenu (créer, éditer, supprimer) et à envoyer un formulaire avec les données adéquates au site.

Faisons un petit schéma pour bien comprendre :

Au départ nous avons deux entités séparées :

- un utilisateur qui est connecté sur le vrai site avec ses identifiants
- un pirate qui va créer un site ou un email frauduleux pour piéger cet utilisateur.

->![Préparation de l'attaque](/media/galleries/304/e617f67c-7b6d-45cc-b446-2f806c1be1d3.png.960x960_q85.jpg)<-

Le fameux lien sur lequel l'utilisateur va cliquer va en fait être un faux site qui ne fera qu'une chose : envoyer une requête pour supprimer tel ou tel contenu.

Or votre contrôleur sait que si tout se passe bien, il doit vous rediriger vers la page de liste par exemple.

Donc vous allez supprimer/ajouter/modifier un contenu sans vous en rendre compte.

Heureusement, il existe une parade.

En session, vous allez enregistrer un nombre généré aléatoirement à chaque fois que vous allez afficher la page.

Sur la page honnête, donc sur le vrai site, vous allez ajouter un champ caché qui s'appellera "csrf_token" par exemple et qui aura pour valeur ce nombre impossible à deviner.

Puis, dans votre contrôleur, vous allez vérifier que ce nombre est bien le même que celui enregistré en session.

Comme ça, tout autre site extérieur qui essaierait de créer une requête sera **immédiatement rejeté** et vous vous en rendrez compte.

Comme faire tout ça, risquerait d'être long à coder à chaque fois, ASP.NET vous aide.

Lorsque vous créez un formulaire de type POST, il suffit d'ajouter deux choses :

- dans le formulaire razor, ajoutez : `@Html.AntiForgeryToken()`;
- au niveau de la méthode `Create`, `Edit` ou `Delete` de votre contrôleur, ajoutez l'attribut `[ValidateAntiForgeryToken]`.

Voilà, vous êtes protégés !

## La faille XSS

La faille "XSS" est une faille de type "injection de code malveillant", elle est néanmoins une des failles les plus connues et les plus faciles à corriger.

Une faille XSS survient lorsqu'une personne essaie d'envoyer du code HTML dans votre formulaire.

Imaginons qu'il envoie `<strong>Je suis important</strong>`. Si vous ne vous protégez pas contre la faille XSS, vous verrez sûrement apparaître la phrase "Je suis important" en gras.
Maintenant, cas un peu plus pernicieux, la personnes vous envoie "</body>je suis important". Et c'est votre design complet qui tombe.

Malheureusement, ça n'est pas tout. La personne peut envoyer un script javascript qui vous redirigera vers un site publicitaire, ou bien illégal. C'est de ce comportement là que vient le nom XSS : Cross Site Scripting.

Comme je vous l'ai dit, la parade est simple : il suffit de remplacer les caractères `><"` par leur équivalent HTML (`&gt; &lt; &quot;`). Comme ça les balises HTML sont considérés comme du texte simple et non plus comme des balises.

Et comme c'est un comportement qui est très souvent désiré, c'est le comportement par défaut de razor quand vous écrivez `@votrevariable`.

Pour changer le comportement, il faut créer un *helper* qui va par exemple autoriser les balises bien construites (`<strong></strong>`), interdire les balises script et les attributs spéciaux (`onclick` par exemple).

[^wiki_csrf]: Plus d'information sur [wikipédia](http://fr.wikipedia.org/wiki/Cross-Site_Request_Forgery)
