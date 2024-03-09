Souvenons-nous de comment fonctionne MVC : le contrôleur *traite des données* puis *génère* une vue ou bien délègue cette génération à un outil dédié.

Explorons un peu ces contrôleurs pour déterminer comment ils fonctionnent.

Tout d'abord, il faut bien comprendre qu'un contrôleur est un objet *comme les autres*. La seule contrainte, c'est qu'il hérite de l'objet `Controller`.

Visual studio possède un certain nombre de guides pour créer un contrôleur. Comme nous sommes encore en train d'apprendre, nous n'allons **pas** utiliser ces guides car ils génèrent beaucoup de code qui ne sont pas adaptés à l'apprentissage pas à pas.

[[a]]
|Assurez vous d'avoir créé un projet "Blog" avec le modèle `MVC` et l'authentification par défaut.

Pour créer un contrôleur, nous allons cliquer droit sur le dossier `Controllers` puis `ajouter`->`Contrôleur`.
Là : sélectionnez "Contrôleur Vide", nommez-le `ArticleController`.

![Ajout d'un nouveau contrôleur](/media/galleries/304/6ade8186-e234-4e09-88b9-914914c5f070.png.960x960_q85.png)

# Qu'est-ce qu'une page

Lorsque vous utilisez MVC, une page correspond en fait à une `action` du contrôleur. Une action, c'est une méthode qui a deux contraintes :

- elle doit être publique
- elle doit retourner un objet `ActionResult`.

Et vous savez quoi? il existe une méthode qui a déjà été codée pour vous dans `Controller`, qui s'appelle `View` et qui vous permet de retourner un `ActionResult` qui contiendra tout le code HTML de votre page.

La seule condition : il faut que dans le dossier `Views`, il y ait un autre dossier qui porte le même nom que votre contrôleur (dans notre exemple `Article`) et qu'ensuite, il y ait un fichier `nom_de_votre_action.cshtml`. Par exemple, pour l'action `Index`, il faut un fichier `Index.cshtml`.

Nous verrons plus tard comment utiliser de manière avancée Razor. Pour l'instant, vous pouvez ne mettre que du code html dans cette page et ça sera parfait.

# Page statique

Les pages statiques ne seront pas les pages les plus nombreuses de votre application, néanmoins, elles peuvent exister. Comme elles sont statiques, une bonne pratique consiste à indiquer au serveur qu'il ne doit pas refaire tout le déroulement de la requête mais aller tout de suite chercher la page déjà créée et la renvoyer à l'utilisateur.
Cela se fait grâce à un filtre appelé [OutputCache](http://msdn.microsoft.com/fr-fr/library/system.web.mvc.outputcacheattribute%28v=vs.118%29.aspx).

```csharp
        // GET: MaPageStatique
        [OutputCache(Duration = 10000000, Order = 1, NoStore = false)]
        public ActionResult MaPageStatique()
        {
            return View();
        }
```
Code: une page statique

# Page dynamique

Les pages dynamiques sont utilisées quand vous voulez mettre en place une page qui change en fonction de l'utilisateur et de l'ancienneté du site.

Prenons en exemple zeste de savoir. Si vous êtes un utilisateur non connecté (on dit aussi *anonyme*), le haut de page vous propose de vous inscrire ou de vous connecter :

->![Bannière pour les anonymes](/media/galleries/304/06725954-750b-4926-aecf-23f42bebdca7.png.960x960_q85.png)<-

Lorsque vous êtes connectés, vous allez par contre pouvoir gérer votre compte.

->![Bannière pour les utilisateurs enregistrés](/media/galleries/304/8c814d4b-cbe2-40fb-8f05-d3c498020865.png.960x960_q85.png)<-

Mais le mieux, c'est que selon que vous soyez utilisateur lambda ou administrateur, vous n'aurez pas accès aux mêmes liens.

->![Menu simple utilisateur](/media/galleries/304/6f7721d7-b551-40a8-9f86-3d552de5cbdb.png.960x960_q85.png) ![Menu administrateur](/media/galleries/304/317f315d-5edd-4d3c-a5bd-e3321663349f.png.960x960_q85.png)
Figure: Les menus utilisateurs et administrateurs sont différents<-

Vous pouvez -comme nous l'avons vu dans notre `Hello Word`- ajouter des données *dynamiquement* de deux manières :

- en donnant à la vue un *Modèle*, dans notre cas ça sera des `Article` ou des `List<Article>` selon notre besoin
- en ajoutant des clefs au `ViewBag` ou au `ViewData`
```csharp
        public ActionResult Index()
        {
            ViewBag.Bla = "bla"; //équivaut à ViewData["bla"] = "bla";
            return View();
        }
```
Le ViewBag et le ViewData sont des propriétés qui font la même chose. Il est conseiller d'utiliser le ViewBag tout simplement parce qu'il respecte plus la notion d'object (ViewBag.TaPropriete), de plus des erreurs de nommage peuvent arriver avec le ViewData.
