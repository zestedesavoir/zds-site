from django import template
from django.urls import reverse

register = template.Library()


@register.filter(name="category_url")
def category_url(category, content):
    _type = content.type.lower()
    return reverse(_type + ":list") + "?tag=" + category.slug
