from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
@stringfilter
def french_typography(str):
    """
    Replaces spaces with non-breaking-spaces or narrow non-breaking-spaces
    before or after some symbols, according to French typography.

    This filter is naive and should not be used on Markdown content.


    Any change here should also be made in assets/js/featured-resource-preview.js
    """
    return mark_safe(
        # Narrow non-breaking space: &#8239;
        str.replace(" ;", "&#8239;;")
        .replace(" ?", "&#8239;?")
        .replace(" !", "&#8239;!")
        .replace(" %", "&#8239;%")
        # Non-breaking space: &nbsp;
        .replace("« ", "«&nbsp;")
        .replace(" »", "&nbsp;»")
        .replace(" :", "&nbsp;:")
    )
