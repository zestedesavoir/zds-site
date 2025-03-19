{% load i18n %}

{% blocktrans with title=title|safe url=url |safe reason=reason %}
Bonjour,

Votre contenu « [{{ title }}]({{ url }}) » a été marqué comme obsolète.

**Justification :**
{{ reason }}

{% endblocktrans %}

{% blocktrans %}
Merci pour votre contribution au site !
{% endblocktrans %}
