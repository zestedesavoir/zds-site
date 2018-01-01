{% load i18n %}

{% trans "Salut !" %}

{% blocktrans with decision=is_granted|yesno:_("acceptée,refusée") hat=hat|safe %}
Tu as demandé la casquette **{{ hat }}** pour ton compte. Ta demande a été {{ decision }}.
{% endblocktrans %}

{% if comment %}
> {{ comment|safe }}
{% endif %}

{% if not solved_by_bot %}
{% trans "Si tu as des questions, n’hésite pas à répondre directement à ce message." %}
{% endif %}
