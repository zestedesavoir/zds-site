from django import template
from django.utils.html import escape, mark_safe
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def highlight(input_string):
    print(input_string)
    stripped_string = input_string.replace("<mark>", "___MARK_TAG___ ")
    stripped_string = stripped_string.replace("</mark>", "___/MARK_TAG___")
    stripped_string = strip_tags(stripped_string)
    stripped_string = stripped_string.replace("___MARK_TAG___", "<mark>")
    stripped_string = stripped_string.replace("___/MARK_TAG___", "</mark>")
    # adding the tag that allows highlighting
    highlighted_string = stripped_string.replace("&lt;mark&gt;", "<mark>").replace("&lt;/mark&gt;", "</mark>")
    print(mark_safe(highlighted_string))
    return mark_safe(highlighted_string)
