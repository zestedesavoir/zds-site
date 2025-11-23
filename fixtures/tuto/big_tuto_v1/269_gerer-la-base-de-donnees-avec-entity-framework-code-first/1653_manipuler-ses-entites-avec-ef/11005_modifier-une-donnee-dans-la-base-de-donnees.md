Ici le cas sera plus "complexe" si je puis dire. En effet, pour s'assurer que quoi qu'il arrive le changement soit bien détecté sans perte de performance (c'est à dire qu'on ne va pas demander au système de comparer caractère par caractère le texte de l'article pour détecter le changement), il faudra forcer un peu les choses.

1. Premièrement, il faudra aller chercher l'objet tel qu'il est stocké en base de données.
1. Ensuite il faudra annoncer à EntityFramework "je vais le modifier".
1. Enfin il faudra mettre en place les nouvelles valeurs.

Tout cela devra être mis dans la méthode "Edit" de votre contrôleur.
