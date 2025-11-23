Vous connaissez la maison maintenant : pour démarrer l'application Web appuyez sur la touche ||F5||. Le serveur va charger notre application sur localhost. Nous devrions tomber sur cette page:

![page d'accueil de notre application](/media/galleries/304/53015f93-22e2-4de7-94a9-8114f1d2a31b.png)

Le navigateur nous affiche une page d’erreur indiquant que la page est introuvable. C'est normal, nous n’avons pas indiqué la route qui correspond à une action de notre contrôleur. Rappelez-vous, nous devons taper l’url suivante : **http://localhost:votre_numero_de_port/Salutation/Index** pour pouvoir appeler la méthode Index du contrôleur SalutationController.

![interface de notre application](/media/galleries/304/8e97dcb4-6831-4566-accb-513c75e3439f.png)

Mettons notre prénom dans le champ de texte et soumettons le formulaire :

->![](/media/galleries/304/429fcc55-d3cc-45b3-b02d-dca126025d27.png)<-

Au moment ou nous soumettons le formulaire, tout le mécanisme s'enclenche et la phrase de bienvenue s'affiche. Si nous affichons le code source de la page ainsi obtenue, nous aurons quelque chose comme :

```html
<!DOCTYPE html>

<html>
<head>
    <meta name="viewport" content="width=device-width" />
    <title>Index</title>
</head>
<body>
    <div>
<form action="/Salutation/Index" method="post">            <h1>BonjourMVC</h1>
            <p>Comment t'appelles-tu jeune Zesteur ?</p>
<input id="prenom_visiteur" name="prenom_visiteur" type="text" value="Arthur" />            <input type="submit" value="Valider" />
</form>        <p>Bonjour &#224; toi, Arthur</p>
    </div>

<!-- Visual Studio Browser Link -->
<script type="application/json" id="__browserLink_initializationData">
    {"appName":"Internet Explorer","requestId":"5c96bb4c6fa5470594489162026a9490"}
</script>
<script type="text/javascript" src="http://localhost:1643/b70ba08d79874a7aa04dc5030e2c2d02/browserLink" async="async"></script>
<!-- End Browser Link -->

</body>
</html>
```

Les contrôles serveurs ont été transformés en HTML avec en complément, les éventuelles valeurs que nous avons mises à jour. Par exemple, le helper `Html.BeginForm` a été transformé en balise `<form>` que vous connaissez bien ou encore le helper `Html.TextBox` s'est lui transformé en `<input type="text ...>`.
