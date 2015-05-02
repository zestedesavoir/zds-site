{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe %}

Bonjour {{ validator }},

La validation de **[{{ title }}]({{ url }})**, que tu avait réservé, a été annulée.

{%  endblocktrans %}