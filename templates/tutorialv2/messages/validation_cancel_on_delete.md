{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe author_url=.get_absolute_url author_name=author.username|safe message=message|safe %}

Bonjour {{ validator }},

La validation de **{{ title }}**, que tu avait réservé, a été annulée par [{{ author_name }}]({{ author_url }}), car il a décidé de le supprimer.

Voici le message qu'il t'as laissé:

{{ message }}

{%  endblocktrans %}