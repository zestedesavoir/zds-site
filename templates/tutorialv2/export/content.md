% {{ content.title|safe|upper }} {% load emarkdown %}{% load profile %}{% load captureas %}
% {% for member in content.authors.all %}{% if not forloop.first %}, {% endif %}{{ member.username }}{% endfor %}
% {{ content.pubdate|date:"d F Y" }}

{% autoescape off %}
{% if content.introduction %}
{% captureas intro %}{{ content.get_introduction|safe }}{% endcaptureas %}
{% if intro.strip != '' %}
# Introduction

{{ intro }}
{% endif %}
{% endif %}

{% for child in content.children %}
# {{ child.title|safe }}
{% if content.has_extracts %} {#  minituto or article #}
{% if child.text %}{{ child.get_text|safe|decale_header_1 }}{% endif %}
{% else %}{# midsize or bigtuto #}
{% if child.introduction %}{{ child.get_introduction|safe|decale_header_1 }}{% endif %}
{% for subchild in child.children %}
## {{ subchild.title|safe }}

{% if child.has_extracts %} {# midsize tuto #}
{% if subchild.text %}{{ subchild.get_text|safe|decale_header_2 }}{% endif %}
{% else %}
{% if subchild.introduction %}{{ subchild.get_introduction|safe|decale_header_2 }}{% endif %}
{% for extract in subchild.children %}

### {{ extract.title|safe }}

{% if extract.text %}{{ extract.get_text|safe|decale_header_3 }}{% endif %}{% endfor %}
{% if subchild.conclusion %}
{% captureas conclu %}{{ subchild.get_conclusion|safe|decale_header_2 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}{% endif %}{% endif %}
{% endif %}{% endfor %}
{% if child.conclusion %}
{% captureas conclu %}{{ child.get_conclusion|safe|decale_header_1 }}{% endcaptureas %}
{% if conclu.strip != '' %}
---------

{{ conclu }}{% endif %}{% endif %}
{% endif %}{% endfor %}
{% if content.conclusion %}
{% captureas conclu %}{{ content.get_conclusion|safe }}{% endcaptureas %}
{% if conclu.strip != '' %}
# Conclusion

{{ conclu }}
{% endif %}
{% endif %}
{% endautoescape %}
