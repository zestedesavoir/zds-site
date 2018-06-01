{% load i18n %}

{% blocktrans with alert_author=alert_author|safe post_author=post_author|safe post_title=post_title|safe post_url=post_url|safe staff_name=staff_name|safe staff_message=staff_message|safe %}
Bonjour {{ alert_author }},

Vous recevez ce message car vous avez signalé le message de *{{ post_author }}* dans le sujet [{{ post_title }}]({{ post_url }}).
Votre alerte a été traitée par **{{ staff_name }}** qui vous a laissé le message suivant :

> {{ staff_message }}

Toute l’équipe de la modération vous remercie !
{% endblocktrans %}
