{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Bonjour {{ user }},

Vous avez été intégré à la rédaction du contenu « [{{ title }}]({{ url }}) ». 
La version brouillon, sur laquelle vous pourrez travailler, est disponible 
[ici]({{ index }}).

Plus rien maintenant ne retient votre plume, alors bon courage !
{%  endblocktrans %}
