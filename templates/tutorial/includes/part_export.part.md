{% load emarkdown %}

{% with tutorial=part.tutorial%}
{% with chapters=part.chapters %}
{% if part.intro %}{{ part.intro }}{% endif %}
{% for chapter in chapters %}
## {{ chapter.title }}
{% for extract in chapter.extracts %}
### {{ extract.title }}
{{ extract.txt|safe|decale_header_3 }}
{% endfor %}
{% endfor %}
{% if part.conclu %}{{ part.conclu }}{% endif %}
{% endwith %}
{% endwith %}
