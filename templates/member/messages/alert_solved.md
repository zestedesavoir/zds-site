{% load i18n %}

{% blocktrans with alert_author=alert_author|safe reported_user=reported_user|safe moderator=moderator|safe staff_message=staff_message|safe %}
Bonjour {{ alert_author }},

Vous recevez ce message car vous avez envoyé un signalement concernant le profil de {{ reported_user }}. L'alerte a été traitée par {{ moderator }} qui vous a laissé le message suivant :

> {{ staff_message }}

Toute l’équipe de modération vous remercie !
{% endblocktrans %}
