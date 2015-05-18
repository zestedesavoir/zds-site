{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Psssst !

Je t'informe que ton {{ type }} « {{ title }} » s'est retrouvé en bêta. 
Il est actuellement à la merci de la communauté, laquelle pourra le 
consulter sans vergogne. Elle pourra également te faire de judicieux 
retours dessus et t'aider à l'améliorer pour satisfaire l'appétit des 
validateurs.

Un sujet dédié à la bêta de ton {{ type }} a été créé automatiquement 
sur le forum et est accessible [ici]({{ url }}). Cours-y vite !
{%  endblocktrans %}
