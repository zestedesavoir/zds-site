# -*- coding: utf-8 -*-

__version__ = '1.0.3'

default_app_config = 'uuslug.apps.AppConfig'

from django.utils import six

if six.PY3:
    from django.utils.encoding import smart_str
else:
    from django.utils.encoding import smart_unicode as smart_str

from slugify import slugify as pyslugify

__all__ = ['slugify', 'uuslug']


def slugify(text, entities=True, decimal=True, hexadecimal=True, max_length=0, word_boundary=False, separator='-'):
    """ Make a slug from a given text """

    return smart_str(pyslugify(text, entities, decimal, hexadecimal, max_length, word_boundary, separator))


def uuslug(s, instance, entities=True, decimal=True, hexadecimal=True,
           slug_field='slug', filter_dict=None, start_no=1, max_length=0,
           word_boundary=False, separator='-'):

    """ This method tries a little harder than django's django.template.defaultfilters.slugify. """

    if hasattr(instance, 'objects'):
        raise Exception("Error: you must pass an instance to uuslug, not a model.")

    queryset = instance.__class__.objects.all()
    if filter_dict:
        queryset = queryset.filter(**filter_dict)
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    slug = slugify(s, entities=entities, decimal=decimal, hexadecimal=hexadecimal,
                   max_length=max_length, word_boundary=word_boundary, separator=separator)

    new_slug = slug
    counter = start_no
    while queryset.filter(**{slug_field: new_slug}).exists():
        if max_length > 0:
            if len(slug) + len(separator) + len(str(counter)) > max_length:
                slug = slug[:max_length - len(slug) - len(separator) - len(str(counter))]
        new_slug = "%s%s%s" % (slug, separator, counter)
        counter += 1

    return new_slug
