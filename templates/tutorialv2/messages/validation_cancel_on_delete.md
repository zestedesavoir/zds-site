{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe user_url=user.get_absolute_url user_name=user.username|safe message=message|safe %}

Bonjour {{ validator }},

La validation de **{{ title }}**, que tu avait réservé, a été annulée par [{{ user_name }}]({{ user_url }}), car il a décidé de le supprimer.

Voici le message qu'il t'as laissé:

{{ message }}

{%  endblocktrans %}