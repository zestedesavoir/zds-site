{% load i18n %}

{% blocktrans with title=content.title|safe type_content=content.textual_type|safe message=message|safe user_name=target_name|safe modo_name=modo_name|safe %}

Bonjour {{ name }},

Ce message fait suite à ton alerte pour les propos de {{ user_name }}
dans {{ type_content }} [{{ title }}]({{ url }}). {{ modo_name }} s'est 
occupé du signalement et t'a déposé un petit mot :

{{ message }}

Toute l'équipe de modération te remercie !

{%  endblocktrans %}
