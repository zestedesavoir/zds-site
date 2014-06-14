from django import template
import re

register = template.Library()


@register.filter(needs_autoescape=False)
def htmltotext(input):
     # remove the newlines
    input = input.replace("\n", " ")
    input = input.replace("\r", " ")
   
    # replace consecutive spaces into a single one
    input = " ".join(input.split())   
   
    # remove all the tags
    p = re.compile(r'<[^<]*?>')
    input = p.sub('', input)
   
    return input