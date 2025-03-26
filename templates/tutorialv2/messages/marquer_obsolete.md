{% load i18n %}

{% blocktrans with title=title|safe url=url |safe reason=reason %}
Bonjour,

Votre contenu « [{{ title }}]({{ url }}) » a été marqué comme obsolète.

**Justification :**
{{ reason }}

{% endblocktrans %}

{% blocktrans %}
Si vous en avez la possibilité, pourriez-vous mettre à jour votre contenu ?
{% endblocktrans %}
