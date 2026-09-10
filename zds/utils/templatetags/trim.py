from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter(name="trim")
def trim(word):
    if word is None:
        return ""
    return word.strip()
