from uuslug import slugify as uuslug_slugify
from uuslug import uuslug as uuslug_uuslug


def wrapper(text):
    """
    Wrapper that removes single quotes from text.
    """
    return text.replace("'", "")


def slugify(text, *args, **kwargs):
    """
    Wrapper around django-uuslug's slugify function
    """
    return uuslug_slugify(wrapper(text), *args, **kwargs)


def uuslug(text, *args, **kwargs):
    """
    Wrapper around django-uuslug's uuslug function
    """
    return uuslug_uuslug(wrapper(text), *args, **kwargs)
