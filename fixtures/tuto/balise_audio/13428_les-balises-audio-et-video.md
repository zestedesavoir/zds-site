# Les balises audio et vidéo

Comme vous le savez, en HTML, tout élément est représenté par une balise. `audio` et `video` ne feront pas exception.

Ces éléments sont de type *block* et sont écrits de la manière suivante :

```html
<audio>
<!-- Des informations sur la piste audio -->
</audio>
```

```html
<video>
<!-- Des informations sur la vidéo -->
</video>
```

# Les éléments importants de ces balises

Bien que leurs buts soient différents, ces deux balises sont très similaires dans leur comportement. Finalement, la seule différence entre un contenu audio et vidéo est que le second *peut* inclure le premier (mais pas nécessairement). Dans un cas comme dans l’autre, on souhaite lire une piste et afficher une interface à l’utilisateur pour interagir avec cette dernière.

Cela nous amène donc au premier attribut indispensable de ces deux balises : la **source**.

## La source

Savoir afficher une balise audio/vidéo c’est bien, mais si on ne lui donne rien à afficher, on n’est pas plus avancé ! Il va donc falloir donner une source à afficher. Tout comme pour une image, elle peut être relative ou absolue. Il existe deux moyens pour la spécifier.

### Via l’attribut `src`

Là encore, comme pour une image, il suffit de spécifier l’attribut `src` pour donner un lien vers la vidéo ou le flux audio à lire.

```html
<video src="http://masource.com/lavideo.avi">
</video>
```

### Via la balise `<source>`

Cependant, il peut être intéressant de proposer plusieurs formats à l’utilisateur. En effet, tous les navigateurs ne savent pas lire tous les formats vidéo. On propose donc la même vidéo dans des formats différents et le navigateur choisira ! Pour cela, on utilise la balise `<source>` *dans* la balise audio/vidéo.

```html
<video>
    <source src="chemin/vers/masource.mp4" type="video/mp4">
    <source src="chemin/vers/masource.ogg" type="video/ogg">
    <source src="chemin/vers/masource.webm" type="video/webm">
</video>
```

Voici une petite démonstration[^source] de ce dernier cas :

->

!(https://jsfiddle.net/tmjosu22/3/)

<-

[[q]]
| Mais c’est pourri, on peut pas lancer la vidéo ! Ça marche pas !

En fait si, tout marche très bien, c'est juste que maintenant que nous avons la vidéo, il va falloir la contrôler…

# Contrôler (simplement) le média

Maintenant que la vidéo est présente, ajoutons un peu d’interactivité à cette dernière…

## Les options « natives »

Les balises multimédia possèdent par défaut quelques attributs bien pratiques. En effet, voici une liste non exhaustive de celles que j'estime être les plus utiles dans l’immédiat :

+ `controls` : permet de rajouter des boutons de contrôle de lecture standards (lecture/pause, barre de progression, plein-écran…) ;
+ `autoplay` : (plutôt évident…) la lecture est lancée automatiquement dès que la vidéo commence à se charger ; n’en abusez pas, cela peut être assez gênant pour la navigation ;
+ `poster` ^*^ : lien vers une image d'illustration si la vidéo n'est pas disponible à l'adresse spécifiée ;
+ `loop` : relance la lecture quand cette dernière est terminée, encore et encore ;
+ `height` et `width` ^*^ : pour spécifier une hauteur et une largeur au lecteur ;
+ `muted` : coupe le son.

~* ne s'applique pas à la balise audio~

Voici par exemple une vidéo avec des contrôles, dont le son est coupé, qui jouera en boucle et dont la taille a été limitée à 320x240 pixels.

```html hl_lines="1"
<video width="320" height="240" controls muted loop>
    <source src="chemin/vers/masource.mp4" type="video/mp4">
    <source src="chemin/vers/masource.ogg" type="video/ogg">
    <source src="chemin/vers/masource.webm" type="video/webm">
</video>
```

->

!(https://jsfiddle.net/tmjosu22/4/)

<-

Vous savez maintenant afficher une vidéo ou jouer un son !

## Encore plus loin, des sous-titres pour les vidéos

Dans notre monde moderne et international, il arrive que les sous-titres puissent être nécessaires pour offrir le contenu à un plus grand public. Et c’est là que la balise `<track>` intervient. Placée dans une balise vidéo, cette dernière proposera des sous-titres au lecteur.

La balise *track* a besoin des informations suivantes :

+ `src` : la source (relative ou absolue) du fichier de sous-titres (au format WebVTT [.vtt](http://dev.w3.org/html5/webvtt/) (WEB Video Text Track)) ;
+ `kind="subtitles"` : pour préciser que l'on parle de sous-titres ;
+ `srclang` : le code international de la langue (en, de, fr…) ;
+ `label` : le nom littéral de la piste de sous-titres.

Par exemple :

```html hl_lines="4-5"
<video controls>
    <source src="ma-super-video.mp4" type="video/mp4">
    <source src="ma-super-video.ogg" type="video/ogg">
    <track src="subtitles_en.vtt" kind="subtitles" srclang="en" label="English">
    <track src="subtitles_fr.vtt" kind="subtitles" srclang="fr" label="Francais">
</video>
```

[[a]]
| À l’heure d’écriture de ce tutoriel, cette balise est encore très peu supportée dans les navigateurs.

## *Fallback*

Si l'utilisateur qui visite votre site possède un navigateur un peu *rétro* ou incomplet vis-à-vis des standards du Web, il serait de bon ton de l’avertir que le contenu ne peut être affiché plutôt que de le laisser attendre indéfiniment un média qui n’arrivera jamais.

Pour cela, il suffit tout simplement d’ajouter du HTML dans la balise média concernée. Si le navigateur ne sait pas interpréter la balise vidéo/audio, alors il ignorera les balises et affichera notre *fallback*. Sinon ce contenu est ignoré car la balise est correctement interprétée.

```html hl_lines="7-9"
<video>
    <!-- Une source quelconque -->
    <source src="…">

    <!-- Ce paragraphe ne s'affichera que dans le cas où le navigateur
         ne sait pas interpréter la balise vidéo -->
    <p class="alert">
        Votre navigateur ne supporte pas la balise vidéo ! Mettez-vous à jour !
    </p>
</video>
```

[[i]]
| Plutôt que d’afficher du texte, vous pouvez très bien aussi afficher un conteneur Flash en solution de secours pour jouer la vidéo. L’idéal est même de proposer une alternative ET les liens de téléchargement de la vidéo, si la licence de distribution de cette dernière le permet.

[^source]: Les vidéos d’exemple sont celles du film [*Big Buck Bunny*](https://peach.blender.org/), un film sous licence Creative Commons.
