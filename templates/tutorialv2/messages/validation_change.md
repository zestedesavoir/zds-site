{% load i18n %}
{% load captureas %}

{% captureas url_list %}
    {% url "validation:list" %}
{% endcaptureas %}

{% blocktrans with title=content.title|safe %}

Bonjour {{ validator }},

Le contenu de **[{{ title }}]({{ url }})**, que tu as réservé, a été mis à 
jour en zone de validation.
Pour voir les modifications apportées, je t'invite à consulter 
[l'historique]({{ url_history }}).

Si tu comptes le valider, il te faudra le réserver à nouveau en te rendant sur 
[la page des validations]({{ url_list }}).

{%  endblocktrans %}

