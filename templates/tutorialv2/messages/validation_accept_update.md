{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url %}

Salut !

La mise à jour de **[{{ title }}]({{ url }})** a été publiée par 
[{{ validator_name }}]({{ validator_url }}), et tout le monde peut désormais 
la découvrir !

{%  endblocktrans %}

