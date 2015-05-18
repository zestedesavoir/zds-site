{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_reject|safe %}

Désolé, le contenu « [{{ title }}]({{ url }}) » n'a malheureusement pas 
franchit l’étape de validation.

Mais pas de panique, certaines corrections peuvent sûrement être faites pour 
l'améliorer et lui permettre de passer la validation ultérieurement. 

Pour expliquer ce rejet, [{{ validator_name }}]({{ validator_url }}), le 
validateur, a laissé le message suivant :

{{ message }}

N'hésite pas à lui envoyer un petit message courtois pour discuter de sa 
décision et demander plus de détails si tout cela manque de clarté ou te 
semble injuste !

{% endblocktrans %}
