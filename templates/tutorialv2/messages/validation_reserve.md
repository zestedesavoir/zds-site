{% load i18n %}

{% blocktrans count num_authors=content.authors.count with title=content.title|safe %}

Salut !

Je viens de prendre en charge l’édition de ton contenu, « [{{ title }}]({{ url }}) ».

À bientôt !
{% plural %}
Salut !

Je viens de prendre en charge l’édition de votre contenu, « [{{ title }}]({{ url }}) ».

À bientôt !

{% endblocktrans %}
