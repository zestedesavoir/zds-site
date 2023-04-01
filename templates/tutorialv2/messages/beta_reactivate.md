{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}

Oyez oyez les agrumes !

Je vous annonce avec plaisir la ré-ouverture de la bêta du contenu
« {{ title }} » ! Je vous souhaite une agréable lecture à l’adresse
suivante :

-> [Je suis de retour !]({{ url }}) <-

Merci pour votre participation.

{%  endblocktrans %}
