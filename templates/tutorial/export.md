{% load emarkdown %}{% load humanize %}{% load profile %}
% {{ tutorial.title|safe|upper }}
% {% for member in tutorial.authors.all %}{{ member.username|title }}, {% endfor %}
% {{ tutorial.pubdate|date:"d F Y" }}

{% autoescape off %}
{% if tutorial.intro %}
# Introduction
{{ tutorial.intro|safe }}
{% endif %}

{% if tutorial.is_mini %}
{# Small tutorial #}
{% for extract in chapter.extracts %}
# {{ extract.title }}
{% if extract.txt %}
{{ extract.txt|safe|decale_header_1 }}
{% endif %}
{% endfor %}
{% else %}
{# Large tutorial #}

{% if parts %}
{% for part in parts %}
# {{ part.title }}

{% include "tutorial/includes/part_export.part.md" %}
{% endfor %}
{% endif %}

{% endif %}

{% if tutorial.conclu %}
# Conclusion
{{ tutorial.conclu|safe }}
{% endif %}
{% endautoescape %}