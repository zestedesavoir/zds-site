{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url %}

Félicitations !

Le zeste **[{{ title }}]({{ url }})** a été publié par [{{ validator_name }}]({{ validator_url }}) ! Les lecteurs du monde entier peuvent désormais venir le consulter, l'éplucher et réagir à son sujet.
Je conseille de rester à leur écoute afin d'apporter des corrections et/ou compléments: un contenu vivant et à jour est bien plus lu qu'un sujet abandonné !

{%  endblocktrans %}

