{% load i18n %}

{% blocktrans with title=content.title|safe type_content=content.textual_type|safe message=message|safe user_name=target_name|safe modo_name=modo_name|safe %}

Bonjour {{ name }},

Vous recevez ce message car vous avez signalé le message de *{{ user_name }}*
dans {{ type_content }} [{{ title }}]({{ url }}). Votre alerte a été traitée 
par **{{ modo_name }}** et il vous a laissé le message suivant :

{{ message }}

Toute l'équipe de la modération vous remercie !

{%  endblocktrans %}
