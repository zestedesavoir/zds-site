{% load i18n %}

{% blocktrans with title=title|safe url=url|safe report_interface_url=report_interface_url raison=raison %}
Bonjour,

Le contenu « [{{ title }}]({{ url }}) » a été signalé comme obsolète.

**Raison du signalement :** {{ raison }}

**Accédez à l’interface de gestion des signalements :** [Gérer les signalements]({{ report_interface_url }})

Merci pour votre contribution à la qualité du site.
{% endblocktrans %}
