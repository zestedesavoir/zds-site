{% load i18n %}

{% blocktrans with title=content.title|safe admin_name=admin.username|safe admin_url=admin.get_absolute_url message=message_reject|safe %}

Désolé, « [{{ title }}]({{ url }}) » a malheureusement été retiré de la liste des billets choisis par
[{{ admin_name }}]({{ admin_url }}) pour la raison suivante :

{{ message }}

N’hésitez surtout pas à contacter cette personne pour lui demander de
vous expliquer son choix et de vous conseiller pour remédier à cela.

{% endblocktrans %}
