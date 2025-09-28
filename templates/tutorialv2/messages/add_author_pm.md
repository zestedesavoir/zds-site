{% load i18n %}

{% blocktrans with title=content.title|safe user=user|safe %}
Bonjour {{ user }},

Vous avez été intégré à la rédaction de « [{{ title }}]({{ url }}) ».
Vous pouvez retrouver ce lien dans votre [liste de publications]({{ index }}).

Plus rien maintenant ne retient votre plume, alors bon courage !
{%  endblocktrans %}
