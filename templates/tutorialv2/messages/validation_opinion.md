{% load i18n %}


{% blocktrans with title=title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_validation|safe %}
Félicitations !

Le billet « [{{ title }}]({{ url }}) » a bien été approuvé par l’équipe du site !
{% endblocktrans %}


{% blocktrans %}
Fêtons-donc ça avec un smoothie ! :D
{% endblocktrans %}
