{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Bonjour,

Vous venez de mettre votre {{ type }} « {{ title }} » en bêta. La communauté 
pourra le consulter afin de vous faire des retours constructifs avant sa 
soumission en validation.

Un sujet dédié pour la bêta de votre {{ type }} a été créé automatiquement 
dans le forum et [est accessible ici]({{ url }}).
{%  endblocktrans %}
