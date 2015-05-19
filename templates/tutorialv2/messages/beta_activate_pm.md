{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Bonjour {{ user }},

Le contenu « {{ title }} » a été passé en bêta. La communauté pourra 
consulter cette version et vous faire de judicieux retours dessus. Elle vous 
permettra ainsi de l'améliorer et de satisfaire les critères de validation.

Pour cela, un sujet a été créé automatiquement sur le forum et est accessible 
[ici]({{ url }}).
{%  endblocktrans %}
