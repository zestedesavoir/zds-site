{% load i18n %}
{% load captureas %}

{% captureas url_list %}
    {% url "validation:list" %}
{% endcaptureas %}

{% blocktrans with title=content.title|safe %}

Ça pulpe {{ validator }} ?

Je suis là pour t'informer que le contenu « [{{ title }}]({{ url }}) » que tu 
as réservé a fait l'objet d'une mise à jour puis d'une mise en validation. La 
version dont tu t'occupes — avec douceur, j'en suis certaine —, apparaît donc comme 
obsolète.

Pour constater les dégâts, euh... les modifications apportées, 
je t'invite à consulter [l'historique]({{ url_history }}).

Enfin, sache que si tu comptes valider cette dernière version, il te faudra 
réserver derechef le contenu, en te rendant sur 
[la page des validations]({{ url_list }}).

{%  endblocktrans %}

