{% spaceless %}
{% load i18n %}
{% load captureas %}
{% load feminize %}
{% captureas level %}{{ target.get_level_as_string|lower }}{% endcaptureas %}
{% captureas feminized %}{{"le"|feminize:level}}{% endcaptureas %}
{% if public %}
    {% captureas content_url %} {{ content.get_absolute_url_online }} {% endcaptureas %}
    {% captureas target_url %} {{ target.get_absolute_url_online }} {% endcaptureas %}
    {% captureas state %} {% endcaptureas %}
{% else %}
    {% captureas content_url %} {{ content.get_absolute_url_beta }} {% endcaptureas %}
    {% captureas target_url %} {{ target.get_absolute_url_beta }} {% endcaptureas %}
    {% captureas state %} {% trans "en bêta" %} {% endcaptureas %}
{% endif %}



{% blocktrans with username=user.username|safe title=content.title|safe type=type|safe %}
Salut !

Il me semble avoir déniché une erreur dans {{ type }} « [{{ title }}]({{ content_url }}) ».{% endblocktrans %}
{% if target != content %}
{% blocktrans with title=target.title|safe %}Fourbe, elle se situe sournoisement dans {{ feminized }} {{ level }} « [{{ title }}]({{ target_url }}) ».{% endblocktrans %}
{% endif %}
{{ text|safe }}
{% endspaceless %}
