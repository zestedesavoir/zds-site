# coding: utf-8

import os
import string
import uuid


THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80

MEDIUM_MAX_WIDTH = 200
MEDIUM_MAX_HEIGHT = 200 

def image_path(instance, filename):
    '''Return path to an image'''
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)

def thumb_path(instance, filename):
    '''Return path to an image'''
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)

def medium_path(instance, filename):
    '''Return path to an image'''
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model
    May be used in a model.save() method.
    """
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old