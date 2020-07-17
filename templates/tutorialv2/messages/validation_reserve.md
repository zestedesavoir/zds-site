{% load i18n %}

{% blocktrans count num_authors=content.authors.count with title=content.title|safe %}

Salut !

Je viens de prendre en charge la validation de ton contenu, « [{{ title }}]({{ url }}) ».

À bientôt !
{% plural %}
Salut !

Je viens de prendre en charge la validation de votre contenu, « [{{ title }}]({{ url }}) ».

À bientôt !

{% endblocktrans %}
