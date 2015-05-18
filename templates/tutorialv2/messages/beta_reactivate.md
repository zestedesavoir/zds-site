{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}

Oyez oyez !

C'est dans la joie et la bonne humeur que je vous annonce la 
ré-ouverture de la bêta du contenu « {{ title }} » ! Je vous 
souhaite une plaisante relecture à l'adresse suivante :

-> [Moi, c'est la bêta. À qui ai-je l'honneur ?]({{ url }}) <-

Mille mercis pour votre charitable participation.

{%  endblocktrans %}
