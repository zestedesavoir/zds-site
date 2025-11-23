Lorsque l’on a un média, on peut avoir envie d'interagir un peu plus avec que simplement afficher les contrôles de base. Nous ferons alors appel à JavaScript pour rentrer dans les entrailles du lecteur…

Imaginons que nous voulions proposer un lecteur sans contrôles natifs, mais uniquement avec nos boutons HTML que nous pourrions styliser via du CSS. Il faudrait alors que ces boutons interagissent avec la vidéo correctement. Admettons que nous voulions ajouter les contrôles suivants :

+ `Lecture` : lit la vidéo ;
+ `Pause` : met la vidéo en pause ;
+ `Stop` : arrête la vidéo ;
+ `-10s` : recule la vidéo de 10 secondes ;
+ `+10s` : avance la vidéo de 10 secondes ;

## Structure de base

Voici la structure de base que nous allons respecter :

```html
<video id="mavideo" controls>
    <source src="http://clips.vorwaerts-gmbh.de/VfE_html5.mp4" type="video/mp4">
    <source src="http://clips.vorwaerts-gmbh.de/VfE.webm" type="video/webm">
    <source src="http://clips.vorwaerts-gmbh.de/VfE.ogv" type="video/ogg">

    <p class="alert">
        Votre navigateur ne supporte pas la balise vidéo ! Mettez-vous à jour !
    </p>
</video>
<div class="controles" hidden>
</div>
```

```javascript
function lecture() {
    // Lit la vidéo
}

function pause() {
    // Met la vidéo en pause
}

function stop() {
    // Arrête la vidéo
}

function avancer(duree) {
    // Avance de 'duree' secondes
}

function reculer(duree) {
    // Recule de 'duree' secondes
}

function creerBoutons() {
    // Crée les boutons de gestion du lecteur
}
```

->

!(https://jsfiddle.net/tmjosu22/8/)

<-

## Mettre nos contrôleurs

Comme vous pouvez le voir dans le squelette précédent, pour l'instant, aucun bouton personnalisé n’est présent sur notre page et la vidéo possède l’interface par défaut. En effet, nous allons créer les boutons dynamiquement en JavaScript dans la fonction `creerBoutons()` qui sera exécutée à la fin du chargement de la page. De cette manière, un utilisateur désactivant le JavaScript pourra tout de même utiliser le navigateur avec l’interface standard.

Voici comment nous allons créer nos boutons. Je compte sur vous pour comprendre sans explication, juste avec les commentaires ! ;)

```javascript
var lecteur;

function creerBoutons() {
    // Crée les boutons de gestion du lecteur
    var btnLecture = document.createElement("button");
    var btnPause = document.createElement("button");
    var btnStop = document.createElement("button");
    var btnReculer = document.createElement("button");
    var btnAvancer = document.createElement("button");

    var controlesBox = document.getElementById("controles");
    lecteur = document.getElementById("mavideo");

    // Ajoute un peu de texte
    btnLecture.textContent = "Lecture";
    btnPause.textContent = "Pause";
    btnStop.textContent = "Stop";
    btnReculer.textContent = "-10s";
    btnAvancer.textContent = "+10s";

    // Ajoute les boutons à l'interface
    controlesBox.appendChild(btnLecture);
    controlesBox.appendChild(btnPause);
    controlesBox.appendChild(btnStop);
    controlesBox.appendChild(btnReculer);
    controlesBox.appendChild(btnAvancer);

    // Lie les fonctions aux boutons
    btnLecture.addEventListener("click", lecture, false);
    btnPause.addEventListener("click", pause, false);
    btnStop.addEventListener("click", stop, false);
    btnReculer.addEventListener("click", function(){reculer(10)}, false);
    btnAvancer.addEventListener("click", function(){avancer(10)}, false);

    // Affiche les nouveaux boutons et supprime l'interface originale
    controlesBox.removeAttribute("hidden");
    lecteur.removeAttribute("controls");
}

// Crée les boutons lorsque le DOM est chargé
document.addEventListener('DOMContentLoaded', creerBoutons, false);
```

->

!(https://jsfiddle.net/tmjosu22/11/)

<-

## Interagir avec la vidéo

Maintenant que nous avons un squelette, nous allons devoir faire appel aux propriétés de l'objet vidéo pour interagir avec (son id est « mavideo »). Pour cela, on ira chercher dans la référence de l’élément : [HTMLMediaElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement). Vous y trouverez les attributs accessibles (dont certains ont été vus plus tôt) ainsi que les méthodes que nous pouvons appeler.

Ainsi nous trouverons par exemple les éléments suivants :

+ `play()` : pour lire la vidéo ;
+ `pause()` : pour la mettre en pause ;
+ `currentTime` : attribut représentant le minutage actuel de la vidéo (*position* dans la vidéo).

On va alors pouvoir implémenter les méthodes JavaScript proposées plus tôt !

```javascript
function lecture() {
    // Lit la vidéo
    lecteur.play();
}

function pause() {
    // Met la vidéo en pause
    lecteur.pause();
}

function stop() {
    // Arrête la vidéo
    // On met en pause
    lecteur.pause();
    // Et on se remet au départ
    lecteur.currentTime = 0;
}

function avancer(duree) {
    // Avance de 'duree' secondes
    // On parse en entier pour être sûr d'avoir un nombre
    lecteur.currentTime += parseInt(duree);
}

function reculer(duree) {
    // Recule de 'duree' secondes
    // On parse en entier pour être sûr d'avoir un nombre
    lecteur.currentTime -= parseInt(duree);
}
```

->

!(https://jsfiddle.net/tmjosu22/15/)

<-
