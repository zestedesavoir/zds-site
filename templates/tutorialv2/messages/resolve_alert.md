{% load i18n %}

{% blocktrans with title=content.title|safe type_content=content.textual_type|safe message=message|safe username=target_name|safe modo_name=modo_name|safe name=name|safe alert_text=alert_text|safe %}

Bonjour {{ name }},

Ce message fait suite à votre alerte concernant les propos de {{ username }}
dans {{ type_content }} [{{ title }}]({{ url }}) :

{{ alert_text }}

{{ modo_name }} s’est occupé du signalement et vous a déposé un petit mot :

{{ message }}

Toute l’équipe de modération vous remercie et vous offre un smoothie !

{%  endblocktrans %}
