from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter('non_breaking_space')
@stringfilter
def non_breaking_space(str):
    # Narrow non-breaking space: &#8239;
    str = str.replace(' ;', '&#8239;;')
    str = str.replace(' ?', '&#8239;?')
    str = str.replace(' !', '&#8239;!')
    str = str.replace(' %', '&#8239;%')

    # Non-breaking space: &nbsp;
    str = str.replace('« ', '«&nbsp;')
    str = str.replace(' »', '&nbsp;»')
    str = str.replace(' :', '&nbsp;:')

    return mark_safe(str)