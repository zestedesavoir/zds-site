{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe user=user|safe %}
Bonjour {{ user }},

Le contenu « {{ title }} » a été passé en bêta. La communauté pourra
consulter cette version et vous faire ses retours dessus. Elle vous
permettra ainsi de l’améliorer et de satisfaire aux critères de validation.

Pour cela, un sujet a été créé automatiquement sur le forum et est accessible
[ici]({{ url }}). N’hésitez surtout pas à en personnaliser le premier message !

{%  endblocktrans %}
