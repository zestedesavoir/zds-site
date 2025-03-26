{% load i18n %}

{% blocktrans with title=title|safe url=url|safe report_interface_url=report_interface_url %}
Bonjour,

Le contenu « [{{ title }}]({{ url }}) » a été signalé comme obsolète.

**Accédez à l’interface de gestion des signalements :** [Gérer les signalements]({{ report_interface_url }})

L'interface contient **plusieurs signalements**, y compris certains qui ont déjà été traités.
Vous pouvez **chercher ce signalement spécifique** ou traiter d'autres signalements en attente.

Merci pour votre contribution à la qualité du site.
{% endblocktrans %}
