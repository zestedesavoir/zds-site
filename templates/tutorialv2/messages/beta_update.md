{% load i18n %}

{% blocktrans with title=content.title|safe %}

Bonjour les agrumes !

La bêta a été mise à jour et décante sa pulpe
à l’adresse suivante :

-> [{{ title}}]({{ url }}) <-

Merci d’avance pour vos commentaires.

{%  endblocktrans %}
