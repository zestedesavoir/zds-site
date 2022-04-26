{% load captureas %}
{% load emarkdown %}
{% autoescape off %}
{% if content.introduction %}
{% captureas intro %}{{ content.get_introduction|safe }}{% endcaptureas %}
{% if intro.strip != '' %}

{{ intro }}
{% endif %} {# intro.strip != '' #}
{% endif %} {# content.introduction #}

{% for child in content.children %}
{% if content.has_extracts or child.ready_to_publish %}
# {{ child.title|safe }}
{% if content.has_extracts %} {# minituto, article or opinion #}
{% if child.text %}{{ child.get_text|safe|shift_heading_1 }}{% endif %}
{% elif child.ready_to_publish %} {# midsize or bigtuto #}
{% if child.introduction %}{{ child.get_introduction|safe|shift_heading_1 }}{% endif %}
{% for subchild in child.children %}
{% if child.has_extracts or subchild.ready_to_publish %}
## {{ subchild.title|safe }}

{% if child.has_extracts %} {# midsize tuto #}
{% if subchild.text %}{{ subchild.get_text|safe|shift_heading_2 }}{% endif %}
{% elif subchild.ready_to_publish %} {# bigtuto #}
{% if subchild.introduction %}{{ subchild.get_introduction|safe|shift_heading_2 }}{% endif %}
{% for extract in subchild.children %}

### {{ extract.title|safe }}

{% if extract.text %}{{ extract.get_text|safe|shift_heading_3 }}{% endif %}
{% endfor %} {# extract in subchild.children #}
{% if subchild.conclusion %}
{% captureas conclu %}{{ subchild.get_conclusion|safe|shift_heading_2 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}
{% endif %} {# conclu.strip != '' #}
{% endif %} {# subchild.conclusion #}
{% endif %} {# subchild.ready_to_publish #}
{% endif %} {# child.has_extracts or subchild.ready_to_publish #}
{% endfor %} {# subchild in child.children #}
{% if child.conclusion %}
{% captureas conclu %}{{ child.get_conclusion|safe|shift_heading_1 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}
{% endif %} {# conclu.strip != '' #}
{% endif %} {# child.conclusion #}
{% endif %} {# child.ready_to_publish #}
{% endif %} {# content.has_extracts or child.ready_to_publish #}
{% endfor %} {# child in content.children #}
{% if content.conclusion %}
{% captureas conclu %}{{ content.get_conclusion|safe }}{% endcaptureas %}
{% if conclu.strip != '' %}

---------

{{ conclu }}
{% endif %} {# conclu.strip != '' #}
{% endif %} {# content.conclusion #}
{% endautoescape %}
