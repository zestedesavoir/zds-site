{% load captureas %}
{% load emarkdown %}
{% autoescape off %}
{% if content.introduction %}
{% captureas intro %}{{ content.get_introduction|safe }}{% endcaptureas %}
{% if intro.strip != '' %}

{{ intro }}
{% endif %}
{% endif %}

{% for child in content.children %}
# {{ child.title|safe }}
{% if content.has_extracts %} {#  minituto or article #}
{% if child.text %}<div class="extract-wrapper">{{ child.get_text|safe|shift_heading_1 }}</div>{% endif %}
{% elif child.ready_to_publish %}{# midsize or bigtuto #}
{% if child.introduction %}{{ child.get_introduction|safe|shift_heading_1 }}{% endif %}
{% for subchild in child.children %}
## {{ subchild.title|safe }}

{% if child.has_extracts %} {# midsize tuto #}
{% if subchild.text %}<div class="extract-wrapper">{{ subchild.get_text|safe|shift_heading_2 }}</div>{% endif %}
{% elif subchild.ready_to_publish %}
{% if subchild.introduction %}{{ subchild.get_introduction|safe|shift_heading_2 }}{% endif %}
{% for extract in subchild.children %}

### {{ extract.title|safe }}

{% if extract.text %}<div class="extract-wrapper">{{ extract.get_text|safe|shift_heading_3 }}</div>{% endif %}{% endfor %}
{% if subchild.conclusion %}
{% captureas conclu %}{{ subchild.get_conclusion|safe|shift_heading_2 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}{% endif %}{% endif %}
{% endif %}{% endfor %}
{% if child.conclusion %}
{% captureas conclu %}{{ child.get_conclusion|safe|shift_heading_1 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}{% endif %}{% endif %}
{% endif %}{% endfor %}
{% if content.conclusion %}
{% captureas conclu %}{{ content.get_conclusion|safe }}{% endcaptureas %}
{% if conclu.strip != '' %}

---------

{{ conclu }}
{% endif %}
{% endif %}
{% endautoescape %}
