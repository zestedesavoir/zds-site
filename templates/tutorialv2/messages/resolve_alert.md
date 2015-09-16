{% load i18n %}

{% blocktrans with title=content.title|safe type_content=content.textual_type|safe message=message|safe user_name=target_name|safe modo_name=modo_name|safe alert_text=alert_text|safe %}

Bonjour {{ name }},

Ce message fait suite à votre alerte concernant les propos de {{ user_name }}
dans {{ type_content }} [{{ title }}]({{ url }}) :

{{alert_text}}

{{ modo_name }} s'est occupé du signalement et vous a déposé un petit mot :

{{ message }}

Toute l'équipe de modération vous remercie et vous offre un smoothie !

{%  endblocktrans %}
