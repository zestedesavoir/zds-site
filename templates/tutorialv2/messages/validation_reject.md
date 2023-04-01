{% load i18n %}

{% blocktrans with title=content.title|safe validator_name=validator.username|safe validator_url=validator.get_absolute_url message=message_reject|safe %}

Désolé, votre contenu « [{{ title }}]({{ url }}) » n’a malheureusement pas
franchi l’étape de validation.

Mais pas de panique, certaines corrections peuvent sûrement être faites
pour l’améliorer et remédier à cela. Vous pouvez commencer par regarder
les raisons de ce rejet, fournies ci-dessous par
[{{ validator_name }}]({{ validator_url }}), le validateur en charge de
votre contenu :

{{ message }}

Si certains points vous semblent obscurs, voire injustes, vous êtes invité à
contacter le validateur pour lui en parler. Il sera ravi de vous fournir des
détails ainsi que des conseils. N’oubliez pas non plus que la communauté peut
vous aider à travers le système de bêta.

{% endblocktrans %}
