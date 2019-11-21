{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été ajouté à la liste des contributeurs {{type}} « {{ title }} », en tant que {{role}}.

Merci pour votre participation !
{%  endblocktrans %}
