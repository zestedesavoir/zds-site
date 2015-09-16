{% load i18n %}

{% blocktrans with title=content.title %}

Bonjour les agrumes !

La bêta {{ type }} « {{ title }} » a été mise à jour et coule sa pulpe 
à l'adresse suivante :

-> [Oh ça va, personne n'est pressé.]({{ url }}) <-

Merci d'avance pour vos commentaires.

{%  endblocktrans %}

