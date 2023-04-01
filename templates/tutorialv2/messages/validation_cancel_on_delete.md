{% load i18n %}
{% load captureas %}

{% blocktrans with title=content.title|safe user_url=user.get_absolute_url user_name=user.username|safe message=message|safe validator=validator|safe %}

Bonjour {{ validator }},

Je t’informe que la validation du contenu « {{ title }} » que tu as réservé, a
été annulée, pour la simple et bonne raison
que le contenu en question a été supprimé par
[{{ user_name }}]({{ user_url }}), qui a fourni l’explication suivante :

{{ message }}

{%  endblocktrans %}
