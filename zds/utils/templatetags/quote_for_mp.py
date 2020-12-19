from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def quote_for_mp(message):
    """
    Return message as a quote
    """
    if message:
        return "> " + message.replace("\n", "\n>")
