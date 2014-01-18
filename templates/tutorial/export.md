{% load emarkdown %}{% load humane_date %}{% load profile %}{% load markup %}

{% if tutorial.image %}![]({{tutorial.image.thumb.url }}){% endif %}
Tutoriel {% if not tutorial.is_mini %}étendu{% endif %} rédigé par :
{% for member in tutorial.authors.all %}
{% with profile=member|profile %}
* [{{ member.username }}]({{ member.get_absolute_url }})
{% endwith %}
{% endfor %}

Catégories du tutoriel :
{% for category in tutorial.subcategory.all %}
* {{ category.title }}
{% endfor %}

{% if tutorial.intro %}
{{ tutorial.intro|safe }}
{% endif %}

{% if tutorial.is_mini %}
{# Small tutorial #}
{% for extract in chapter.extracts %}
#[{{ extract.title }}](#{{ extract.position_in_chapter }}-{{ extract.title|slugify }})
{% if extract.txt %}
{{ extract.txt|safe }}
{% endif %}
{% endfor %}
{% else %}
{# Large tutorial #}

{% if parts %}
{% for part in parts %}
#[Partie {{ part.position_in_tutorial }} : {{ part.title }}]({% url "view-part-url-online" tutorial.pk tutorial.slug part.slug %})

{% include "tutorial/view_part_export_common.part.md" %}
{% endfor %}
{% endif %}

{% endif %}

{% if tutorial.conclu %}
{{ tutorial.conclu|safe }}
{% endif %}