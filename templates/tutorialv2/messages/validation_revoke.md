{% load i18n %}

{% blocktrans with title=content.title|safe admin_name=admin.username|safe admin_url=admin.get_absolute_url message=message_reject|safe %}

Désolé, « [{{ title }}]({{ url }}) » a malheureusement été dépublié par 
[{{ admin_name }}]({{ admin_url }}) pour la raison suivante :

{{ message }}

N'hésite en aucun cas à contacter cette personne ; elle sera ravie de 
t'expliquer son choix et de te conseiller pour remédier à cela.

{% endblocktrans %}
