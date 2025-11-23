{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe user_url=user.get_absolute_url user_name=user.username|safe message=message|safe validator=validator|safe %}

Bonjour {{ validator }},

Je t’informe de l'annulation de la mise en validation du contenu
« [{{ title }}]({{ url }}) », que tu avais réservé. La raison suivante est
fournie par [{{ user_name }}]({{ user_url }}) :

{{ message }}

{%  endblocktrans %}
