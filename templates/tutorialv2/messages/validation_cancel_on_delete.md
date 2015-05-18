{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe user_url=user.get_absolute_url user_name=user.username|safe message=message|safe %}

Bonjour {{ validator }},

La validation du contenu **{{ title }}**, que tu as réservé, a été annulée 
parce que le contenu a été supprimé par [{{ user_name }}]({{ user_url }}). La 
raison est la suivante :

{{ message }}

{%  endblocktrans %}
