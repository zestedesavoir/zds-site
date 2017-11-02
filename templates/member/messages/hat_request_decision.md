{% load i18n %}

{% trans "Bonjour," %}

{% blocktrans with decision=is_granted|yesno:_("acceptée,refusée") moderator_name=moderator.username|safe moderator_url=moderator.profile.get_absolute_url hat=hat|safe %}
Vous avez demandé la casquette **{{ hat }}** pour votre compte. Votre demande a été {{ decision }} par [{{ moderator_name }}]({{ moderator_url }}).
{% endblocktrans %}

{% if comment %}
> {{ comment|safe }}
{% endif %}

{% trans "L’équipe" %} {{ site_name|safe }}
