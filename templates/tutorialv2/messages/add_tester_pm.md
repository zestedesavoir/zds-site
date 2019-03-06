{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été ajouté à la liste des testeurs du contenu en cours de rédaction « [{{ title }}]({{ url }}) ». 
Il a été ajouté à la liste de vos contenus en rédaction 
[ici]({{ index }}).

Bonne lecture !
{%  endblocktrans %}
