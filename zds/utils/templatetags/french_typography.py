from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
@stringfilter
def french_typography(str):
    return mark_safe(
        # Narrow non-breaking space: &#8239;
        str.replace(' ;', '&#8239;;')
           .replace(' ?', '&#8239;?')
           .replace(' !', '&#8239;!')
           .replace(' %', '&#8239;%')
        # Non-breaking space: &nbsp;
           .replace('« ', '«&nbsp;')
           .replace(' »', '&nbsp;»')
           .replace(' :', '&nbsp;:')
    )
