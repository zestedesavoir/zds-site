{% load i18n %}

{% blocktrans with title=content.title|safe %}

Bonjour {{ name }}

Vous recevez ce message car vous avez signalé le message de *{{ target_name }}*
dans {{ content.textual_type|safe }} [{{ title }}]({{ url }}). Votre alerte a été traitée par **{{ modo_name }}**
et il vous a laissé le message suivant :


> {{ message }}

Toute l'équipe de la modération vous remercie !

{%  endblocktrans %}
