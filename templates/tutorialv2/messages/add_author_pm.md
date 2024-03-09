{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été intégré à la rédaction du contenu « [{{ title }}]({{ url }}) ».
Il a été ajouté à la liste de vos contenus en rédaction
[ici]({{ index }}).

Plus rien maintenant ne retient votre plume, alors bon courage !
{%  endblocktrans %}
