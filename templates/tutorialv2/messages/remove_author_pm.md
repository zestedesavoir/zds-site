{% load i18n %}

{% blocktrans with title=content.title|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été retiré de la rédaction de « {{ title }} ».

{%  endblocktrans %}
