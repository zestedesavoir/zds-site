{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_validation|safe %}

Ouaiiiiis !

La mise à jour de « [{{ title }}]({{ url }}) » a été publiée.
Tout le monde peut désormais découvrir la toute dernière version de votre contenu !
Son validateur, [{{ validator_name }}]({{ validator_url }}), vous laisse le message suivant :

{{ message }}

Vous avez bien mérité un smoothie. :D

{%  endblocktrans %}

