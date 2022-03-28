# Mainly based on django-email-obfuscator (https://github.com/morninj/django-email-obfuscator - MIT Licence)
# https://github.com/morninj/django-email-obfuscator/blob/master/email_obfuscator/templatetags/email_obfuscator.py

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


def obfuscate_string(value):
    return "".join([f"&#{str(ord(char)):s};" for char in value])


@register.filter
@stringfilter
def obfuscate(value):
    return mark_safe(obfuscate_string(value))


@register.filter
@stringfilter
def obfuscate_mailto(value, text=None):
    mail = obfuscate_string(value)

    if text:
        link_text = text
    else:
        link_text = mail

    return mark_safe('<a href="{:s}{:s}">{:s}</a>'.format(obfuscate_string("mailto:"), mail, link_text))


@register.filter
@stringfilter
def obfuscate_mailto_top_subject(value, subject=None):
    mail = obfuscate_string(value)

    if subject:
        txt = obfuscate_string(f"?Subject={subject}")
    else:
        txt = ""

    return mark_safe('<a href="{}{}{}" target="_top">{}</a>'.format(obfuscate_string("mailto:"), mail, txt, mail))
