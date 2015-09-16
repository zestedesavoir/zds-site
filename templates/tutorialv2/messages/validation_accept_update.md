{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url %}

Ouaiiiiis !

La mise à jour de « [{{ title }}]({{ url }}) » a été publiée par 
[{{ validator_name }}]({{ validator_url }}). Tout le monde peut désormais 
découvrir la toute dernière version de votre contenu !

Vous avez bien mérité un smoothie. :D

{%  endblocktrans %}

