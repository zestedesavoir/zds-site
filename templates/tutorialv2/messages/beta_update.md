{% load i18n %}

{% blocktrans with title=content.title %}

Bonjour,

La bêta de votre {{ type }} « {{ title }} » a été mise à jour et 
trépigne d'impatience à l'adresse suivante :

-> [Bêta mais pas bête !]({{ url }}) <-

Merci d'avance pour vos commentaires et bon courage avec elle.

{%  endblocktrans %}

