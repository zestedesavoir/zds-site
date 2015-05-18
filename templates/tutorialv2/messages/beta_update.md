{% load i18n %}

{% blocktrans with title=content.title %}

Bonjour,

La bêta du contenu « {{ title }} » a été mise à jour et fait toujours 
l'imbécile à l'adresse suivante :

-> [Bêta mais pas bête !]({{ url }}) <-

Merci d'avance pour vos commentaires et bon courage avec elle.

{%  endblocktrans %}

