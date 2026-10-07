{% load i18n %}

{% blocktrans with title=content.title|safe %}

Félicitations !

Je viens de proposer le billet « [{{ title }}]({{ url }}) » comme article !

Il est en zone d’édition et sera examiné prochainement.

À bientôt !
{% endblocktrans %}
