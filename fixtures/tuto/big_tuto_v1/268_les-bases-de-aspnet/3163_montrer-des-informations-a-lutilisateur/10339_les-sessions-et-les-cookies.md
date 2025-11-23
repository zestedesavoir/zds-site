Vous vous rendrez vite compte d'un problème récurrent lorsqu'on fait du développement web : quand on passe d'une page à l'autre, toutes les données qui n'ont pas été enregistrées "en dur" (dans un fichier ou dans la base de données) sont oubliées.

C'est dû à une propriété de base de HTTP, on dit qu'il est *stateless*.
Ce mot signifie que deux requêtes successives sont indépendantes. Cela permet d'éviter les *effets de bord* qui seraient une source infinie de bug.

Alors comment retenir des informations de pages en pages?

Il existe deux types d'informations :

- les informations qui n'ont d'intérêt que pendant la visite **actuelle** de l'utilisateur. la devise de ces données c'est "Demain est un autre jour".
Pour leur cas particulier, nous utiliserons les **sessions**. C'est par exemple le cas lorsque sur un site de commerce électronique, vous utilisez un panier qui se complète au fur et à mesure.
- les informations qui sont utiles à long terme. Leur devise c'est "souvenir, souvenir". L'exemple le plus parlant est celui de la case que vous cochez dans le formulaire de connexion "se souvenir de moi".

->![Connexion automatique sur ZDS](/media/galleries/304/72135448-e1be-411f-8495-f2bcde9cf1e8.png.960x960_q85.jpg)<-

# Les sessions

Une session, c'est un tableau de données qui ne dure que pendant que l'utilisateur visite votre site.

->![Exemple de tableau de session](/media/galleries/304/333eeed9-c69c-49d2-a428-6569304d6736.png.960x960_q85.png)<-

Pour déterminer que l'utilisateur est en train de visiter votre site, le serveur déclenche un compte à rebours de quelques minutes qui est remis à zéro à chaque fois que vous cliquez sur un lien du site.

->![Fonctionnement d'une session](/media/galleries/304/3f19fd3b-a47e-4ffe-a88b-78fe30346503.png.960x960_q85.jpg)<-

Les données de la sessions sont stockées **du côté du serveur**. Pour associer un utilisateur à une session le serveur utilise un **identifiant de session**. Par défaut cet identifiant est généré aléatoirement selon des standards sécurisés[^entropy]. Vous pouvez définir vous même le moyen de générer les identifiants de session mais, je ne vous dirai pas comment car c'est hautement déconseillé dans 99.99999999% des cas.

Pour manipuler des données en session, il faut utiliser la propriété `Session` de votre contrôleur :

```csharp
        public ActionResult UneActionAvecSession()
        {
            Session["panier"] = "blabla";//on écrit un string dans la clef "panier"
            if (Session["Nombre_Pages_Visitees"] != null)
            {
                Session["Nombre_Pages_Visitees"] = (int)Session["Nombre_Pages_Visitees"] + 1;
            }
            else
            {
                Session["Nombre_Pages_Visitees"] = 1;
            }
            return View();
        }
```
Code : manipulation basique des sessions

Comme vous avez pu le voir, on peut mettre tout et n'importe quoi dans une session.

Cela signifie qu'il **faut** convertir à **chaque fois** les données pour pouvoir les utiliser.

Une façon plus *élégante* serait d'accéder à notre `Session["Nombre_Pages_Visitees"]` à partir d'une propriété, ce qui permettrait d'éviter un mauvais copier/coller de la clef.

[[i]]
| Pour gérer les connexion d'utilisateur, ASP.NET peut utiliser les sessions. Dans ce cas là, vous n'avez pas à vous préoccuper de ce qui se passe en interne, le framework gère tout lui même et ça évite beaucoup de bug.

[[i]]
| Il se peut que vous observiez des clefs qui apparaissent toutes seules mais pour une seule page. On appelle ça des "flashes". Cette technique est très utilisée pour la gestion des erreurs dans les formulaires.

[[a]]
| Par défaut, l'identifiant de session est enregistré dans un **cookie** appellé SESSID. Je vous conseille de laisser ce comportement par défaut tel qu'il est.

[[i]]
|Par défaut, votre navigateur partage la session à tous les onglets qui pointent vers le site web. Pour éviter cela, il faut activer la fonctionnalité "session multiple".

# Les cookies

Pour retenir une information longtemps (la loi oblige un maximum de 13 mois), vous pouvez utiliser un **Cookie**.

Contrairement aux sessions, les cookies sont stockés dans le navigateur du client.

Les cookies sont des simples fichier de texte, ils sont **inoffensifs**. Ils permettent de stocker un petit nombre d'information afin de vous aider à les passer de page en page.

A chaque fois que vous envoyez une requête, les cookies sont envoyés au serveur. Dans ASP.NET vous manipulez les cookies comme une collection spécialisée.

```csharp
        public ActionResult UneActionAvecUnCookie()
        {
            if (Request.Cookies["valeur_simple"] != null) //on vérifie que le cookie existe TOUJOURS
            {
                //obtenir les valeurs
                string valeur = Request.Cookies.Get("valeur_simple").Value;
            }
            //ajouter les valeurs
            //un conseil : toujours mettre Secure à true
            //on peut aussi définir le temps de validité du cookie avec Expires
            Response.Cookies.Set(new HttpCookie("valeur_simple", "blabla") { Secure = true });

            return View();
        }
```
Code: manipulation de base des cookies

Comme on peut le voir ci-dessus, on utilise deux objets différents pour mettre en place des cookies.
Il y a Request qui permet de lire les données du navigateur et Response qui permet de sauvegarder des informations chez le client.

# Mini TP : Un bandeau pour prévenir l'utilisateur?

Ces derniers temps, on parle beaucoup des cookies, et les politiques, les médias, tout le monde s'est emparé du problème.

Cela signifie que vous avez des obligations légales à propos des cookies[^legal]. L'une d'entre elles est de demander à votre visiteur s'il accepte les cookies **dans le cas où ces derniers manipulent des données personnelles**, notamment pour tracer vos faits et gestes.

Les cookies ne sont **pas** dangereux en soi, et il n'est pas interdit d'utiliser des cookies.

Je le répète : seuls certains cookies particuliers[^liste_cookie] nécessitent d'approbation de vos visiteurs pour être utilisés.

Dans ce cas il faut mettre un bandeau dans votre site.

Cela peut être un exercice très intéressant pour vous de mettre en place ce bandeau. Considérez cela comme un mini TP dont la solution se trouve en dessous.

## Quelques indices

Nous allons faire les choses simplement, il y aura qu'un seul contrôleur qui va afficher le bandeau (/Accueil/Index). Le code HTML sera simple, une phrase avec deux liens qui renverrons vers un contrôleur du type /Accueil/Cookies?accept=1 (ou 0)

Voici un petit diagramme qui explique comment les choses doivent se passer :

->![Logique pour la création du bandeau](/media/galleries/304/d7b3324e-25be-4907-8da4-d15fc03fee37.png.960x960_q85.jpg)<-

Comment tester notre solution ?

Ce qu'il faut savoir avant c'est que pour récupérer nos cookies, il ne faut pas être en localhost. Pour changer cela il y a quelques petites manipulations à faire :

- Aller dans les propriétés de son projet puis onglet Web et définir l'Url, [comme sur cette image](http://i.imgur.com/9KyP0m1.png)
- Changer le fichier hosts (C:\Windows\System32\drivers\etc\hosts) et rajouter simplement, 127.0.0.1    livesite.dev
- Modifier applicationhost.config (%USERPROFILE%\My Documents\IISExpress\config\applicationhost.config) et chercher 2693 et remplacer le mot localhost par livesite.dev

```xml
            <site name="Blog" id="VotreID">
                <application path="/" applicationPool="Clr4IntegratedAppPool">
                    <virtualDirectory path="/" physicalPath="VotreChemin" />
                </application>
                <bindings>
                    <binding protocol="http" bindingInformation="*:2693:livesite.dev" />
                </bindings>
            </site>
```

Et voilà on voit notre cookie, [par exemple dans chrome](http://i.imgur.com/IaxqKQS.png)


## Une solution

[[secret]]
| ```csharp
| // GET: Accueil
|         public ActionResult Index()
|         {
|             bool afficheBandeau = true;
|             if (Request.Cookies["autoriser_analyse"] != null)
|             {
|                 afficheBandeau = Request.Cookies.Get("autoriser_analyse").Value == "vrai" ? false : true;
|             }
|             ViewBag.DisplayCookie = afficheBandeau;
|
|             return View();
|         }
|
|         //
|         // GET : /Cookies?accept=1
|         public ActionResult Cookies(int accept)
|         {
|             string autorizeCookies = "faux";
|
|             //Accepte le cookie
|             if (accept == 1)
|             {
|                 autorizeCookies = "vrai";
|             }
|
|             Response.Cookies.Set(new HttpCookie("autoriser_analyse", autorizeCookies) { Expires = DateTime.MaxValue });
|
|             return View("Index");
|         }
| ```
| Code : Le contrôleur
|
| ```html
| <!DOCTYPE html>
|
| <html>
| <head>
|     <meta name="viewport" content="width=device-width" />
|     <title>@ViewBag.Title - Blog</title>
|     <link rel="stylesheet" href="~/Content/Blog.css" type="text/css" />
| </head>
| <body>
|     @{
|         if (ViewBag.DisplayCookie != null)
|         {
|             <div id="cookies-banner" @(ViewBag.DisplayCookie ? "style=display:block;" : "")>
|                 <span>
|                     En poursuivant votre navigation sur ce site, vous nous autorisez à déposer des cookies. Voulez vous accepter ?
|                 </span>
|                 <a href="/Accueil/Cookies?accept=1" id="accept-cookies">Oui</a>
|                 <a href="/Accueil/Cookies?accept=0" id="reject-cookies">Non</a>
|             </div>
|         }
|     }
|
|     <header>
|         <h1>Mon Blog ASP.NET MVC</h1>
|         <ul id="navliste">
|             <li class="premier"><a href="/Accueil/" id="courant">Accueil</a></li>
|             <li><a href="/Article/List/">Blog</a></li>
|             <li><a href="/Accueil/About/">A Propos</a></li>
|         </ul>
|     </header>
|     <div id="corps">
|         @RenderBody()
|     </div>
|     <footer>
|         <p>@DateTime.Now.Year - Mon Blog MVC</p>
|     </footer>
| </body>
| </html>
| ```
| Code : La vue
|
| ```css
|
| /* barre cookie */
|
| #cookies-banner {
|     display: none;
|     background: none repeat scroll 0% 0% #062E41;
|     padding: 0px 2.5%;
| }
|
| #cookies-banner span {
|     display: inline-block;
|     margin: 0px;
|     padding: 7px 0px;
|     color: #EEE;
|     line-height: 23px;
| }
|
| #cookies-banner #reject-cookies {
|     display: inline-block;
|     background: none repeat scroll 0px 0px transparent;
|     border: medium none;
|     text-decoration: underline;
|     margin: 0px;
|     padding: 0px;
|     color: #EEE;
| }
|
| #cookies-banner a {
|     display: inline-block;
|     color: #EEE;
|     padding: 4px 13px;
|     margin-left: 15px;
|     background: none repeat scroll 0% 0% #084561;
|     text-decoration: none;
| }
|
| #cookies-banner #accept-cookies {
|     text-decoration: none;
|     background: none repeat scroll 0% 0% #EEE;
|     color: #084561;
|     padding: 4px 15px;
|     border: medium none;
|     transition: #000 0.15s ease 0s, color 0.15s ease 0s;
|     margin-top: 3px;
| }
|
| /* fin barre cookie */
| ```
| Code : le css
|

[^entropy]: Afin de s'assurer au maximum de la sécurité (dans notre cas de l'unicité de l'identifiant et de la difficulté à le deviner), les algorithmes utilisés demandent une grande [entropie](http://fr.wikipedia.org/wiki/Entropie_de_Shannon).
[^legal]: notamment, un cookie ne doit pas avoir une durée de vie de plus de 13 mois. La liste complète se trouve sur le site de la [CNIL](http://www.cnil.fr/vos-obligations/vos-obligations/).
[^liste_cookie]: [Liste complète](http://www.cnil.fr/vos-obligations/sites-web-cookies-et-autres-traceurs/).
