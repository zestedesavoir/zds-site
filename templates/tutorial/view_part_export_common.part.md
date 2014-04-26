{% load emarkdown %}

{% with tutorial=part.tutorial%}
{% with chapters=part.chapters %}
{% if part.intro %}{{ part.intro|safe }}{% endif %}
{% for chapter in chapters %}
##Chapitre {{ chapter.part.position_in_tutorial }}.{{ chapter.position_in_part }} | {{ chapter.title }}
{% for extract in chapter.extracts %}
###{{ extract.title }}
{{ extract.txt|safe|decale_header|decale_header|decale_header }}
{% endfor %}
{% endfor %}
{% if part.conclu %}{{ part.conclu|safe }}{% endif %}
{% endwith %}
{% endwith %}
