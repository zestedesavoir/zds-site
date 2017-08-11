{% load i18n %}

{% trans "Bonjour," %}

{% blocktrans with decision=is_granted|yesno:_("acceptée,refusée") moderator_name=moderator.username|safe moderator_url=moderator.profile.get_absolute_url %}
Vous avez demandé la casquette **{{ hat }}** pour votre compte. Votre demande a été {{ decision }} par [{{ moderator_name }}]({{ moderator_url }}).
{% endblocktrans %}

{% if comment %}
> {{ comment }}
{% endif %}

{% trans "L'équipe" %} {{ site_name }}
