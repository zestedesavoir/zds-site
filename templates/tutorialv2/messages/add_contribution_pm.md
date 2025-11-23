{% load i18n %}

{% blocktrans with title=content.title|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été ajouté à la liste des contributeurs de la publication « {{ title }} », en tant que {{ role }}.

Merci pour votre participation !
{%  endblocktrans %}
