{% load i18n %}

{% blocktrans with decision=is_granted|yesno:_("acceptée,refusée") moderator_name=moderator.username|safe moderator_url=moderator.get_absolute_url %}

Bonjour,

Vous avez demandé la casquette **{{ hat }}** pour votre compte. Votre demande a été {{ decision }} par [{{ moderator_name }}]({{ moderator_url }}).

N'hésitez pas à contacter cette personne afin d'obtenir plus d'informations sur sa décision.

L'équipe {{ site_name }}
{% endblocktrans %}
