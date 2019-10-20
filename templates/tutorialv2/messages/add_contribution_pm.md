{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été désigné comme relecteur du contenu « [{{ title }}]({{ url }}) ».

Merci pour votre temps accordé à ce contenu !
{%  endblocktrans %}
