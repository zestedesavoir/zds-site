{% load markup %}
{% load emarkdown %}

{% with tutorial=part.tutorial%}
{% with authors=tutorial.authors.all %}
{% with chapters=part.chapters %}            
{% if part.intro %}
{{ part.intro }}
{% endif %}
{% for chapter in chapters %}
##[Chapitre {{ chapter.part.position_in_tutorial }}.{{ chapter.position_in_part }} | {{ chapter.title }}]({% url "view-chapter-url-online" tutorial.pk tutorial.slug part.slug chapter.slug %})
{% for extract in chapter.extracts %}
[{{ extract.title }}]({% url "view-chapter-url-online" tutorial.pk tutorial.slug part.slug chapter.slug %}#{{ extract.position_in_chapter }}-{{ extract.title|slugify }})
{{ extract.txt }}
{% endfor %}
{% endfor %}

{% if part.conclu %}
{{ part.conclu }}
{% endif %}
{% endwith %}
{% endwith %}
{% endwith %}
