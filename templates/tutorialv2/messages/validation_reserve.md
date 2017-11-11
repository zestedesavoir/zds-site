{% load i18n %}

{% blocktrans with title=content.title|safe %}

Salut !

Je viens de prendre en charge la validation de ton contenu, « [{{ title }}]({{ url }}) ».

À bientôt !

{% endblocktrans %}
