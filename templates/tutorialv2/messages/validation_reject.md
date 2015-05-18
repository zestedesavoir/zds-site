{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_reject|safe %}

Désolé, le contenu « [{{ title }}]({{ url }}) » n'a malheureusement pas 
franchi l’étape de validation. 

Mais pas de panique, tout n'est pas perdu : certaines corrections peuvent 
sûrement être faites pour l'améliorer et remédier à ça. Tu peux commencer par 
jeter un oeil aux raisons de ce rejet, fournies ci-dessous par 
[{{ validator_name }}]({{ validator_url }}), validateur de son état :

{{ message }}

Si certains points te semblent obscurs, voire injustes, tu es invité à 
contacter le validateur pour lui en parler. Rassure-toi, ces bêtes-là ne 
mordent pas.

{% endblocktrans %}
