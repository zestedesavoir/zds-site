{% load i18n %}
{% load captureas %}

{% captureas url_list %}
    {% url "validation:list" %}
{% endcaptureas %}

{% blocktrans with title=content.title|safe %}

{{ validator }}, bonjour.

Je ne t'apprends rien en t'informant que tu as réservé le contenu 
« [{{ title }}]({{ url }}) » et tu te demandes pourquoi je te 
raconte ça. Et bien il s'avère que ce contenu a fait l'objet d'une 
mise à jour puis d'une mise en validation. La version dont tu 
t'occupes — avec douceur, j'en suis certain —, apparaît donc comme 
obsolète.

Pour constater les dégâts, euh... les modifications apportées, 
je t'invite à consulter [l'historique]({{ url_history }}).

Enfin, sache que si tu comptes le valider, il te faudra le réserver 
derechef, en te rendant sur [la page des validations]({{ url_list }}).

{%  endblocktrans %}

