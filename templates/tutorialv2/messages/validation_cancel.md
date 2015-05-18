{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe user_url=user.get_absolute_url user_name=user.username|safe message=message|safe %}

Bonjour {{ validator }},

La validation du contenu **[{{ title }}]({{ url }})**, que tu as réservé, a 
été annulée par [{{ user_name }}]({{ user_url }}) pour la raison suivante :

{{ message }}

{%  endblocktrans %}
