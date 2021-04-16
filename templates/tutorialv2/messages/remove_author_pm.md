{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été retiré de la rédaction du contenu « {{ title }} ».

{%  endblocktrans %}
