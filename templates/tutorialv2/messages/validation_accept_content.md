{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url %}

Félicitations !

Le contenu « [{{ title }}]({{ url }}) » a été publié par 
[{{ validator_name }}]({{ validator_url }}) ! Les lecteurs du monde entier 
peuvent désormais le consulter, l'éplucher et réagir à son sujet.

{% if content.is_article %}
Fêtons-donc ça avec un smoothie ! :D
{% else %} 
Je vous conseille de rester à leur écoute afin d'apporter des corrections et/ou 
compléments : un contenu vivant et à jour est fort apprécié des lecteurs 
et bien plus gratifiant pour l'auteur !

Mais avant, fêtons-donc ça avec un smoothie ! :D
{% endif %}


{%  endblocktrans %}

