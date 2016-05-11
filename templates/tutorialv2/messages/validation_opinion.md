{% load i18n %}


{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_validation|safe %}
Félicitations !

Le billet « [{{ title }}]({{ url }}) » a bien été approuvé.
Les lecteurs du monde entier peuvent désormais le consulter, l'éplucher et réagir à son sujet.
{% endblocktrans %}


{% blocktrans %}
Fêtons-donc ça avec un smoothie ! :D
{% endblocktrans %}