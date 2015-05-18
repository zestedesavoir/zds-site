{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Noble {{ user }},

Tu as reçu l'incommensurable privilège de participer à la rédaction du 
contenu « [{{ title }}]({{ url }}) », que tu peux gratifier de ta présence 
[ici]({{ index }}).

Maintenant que plus rien ne retient ta plume, je te souhaite bon courage !
{%  endblocktrans %}
