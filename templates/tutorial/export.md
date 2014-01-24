{% load emarkdown %}{% load humane_date %}{% load profile %}{% load markup %}
% {{ tutorial.title }}
% {% for member in tutorial.authors.all %} {{ member.username }}, {% endfor %}

{% if tutorial.intro %}
#Introduction
{{ tutorial.intro|safe }}
{% endif %}

{% if tutorial.is_mini %}
{# Small tutorial #}
{% for extract in chapter.extracts %}
#{{ extract.title }}
{% if extract.txt %}
{{ extract.txt|safe }}
{% endif %}
{% endfor %}
{% else %}
{# Large tutorial #}

{% if parts %}
{% for part in parts %}
#Partie {{ part.position_in_tutorial }} : {{ part.title }}

{% include "tutorial/view_part_export_common.part.md" %}
{% endfor %}
{% endif %}

{% endif %}

{% if tutorial.conclu %}
#Conclusion
{{ tutorial.conclu|safe }}
{% endif %}