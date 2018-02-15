{% load i18n %}

{% blocktrans with title=content.title|safe %}

Félicitations !

Je viens de promouvoir le billet « [{{ title }}]({{ url }}) » en article !

Il est en validation et sera examiné prochainement.

À bientôt !
{% endblocktrans %}
