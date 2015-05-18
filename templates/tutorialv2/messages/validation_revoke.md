{% load i18n %}

{% blocktrans with title=content.title|safe admin_name=admin.username|safe admin_url=admin.get_absolute_url message=message_reject|safe %}

Désolé, **[{{ title }}]({{ url }})** a malheureusement été dépublié par 
[{{ admin_name }}]({{ admin_url }}). Voici le message qu'il a laissé :

{{ message }}

N'hésite pas a lui envoyer un petit message courtois pour discuter de la 
décision et demander plus de détails si tout cela te semble injuste ou 
manque de clarté !

{% endblocktrans %}
