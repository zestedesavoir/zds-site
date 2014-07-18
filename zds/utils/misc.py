# coding: utf-8

import os
import string
import uuid
import hashlib

THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80

MEDIUM_MAX_WIDTH = 200
MEDIUM_MAX_HEIGHT = 200

def compute_hash(filenames):
    """returns a md5 hexdigest of group of files to check if they have change"""
    md5_hash = hashlib.md5()
    for filename in filenames:
        file_handle = open(filename, 'rb')
        must_continue = True
        while must_continue:
            read_bytes = file_handle.read(8096)
            if not read_bytes:
                must_continue = False
            else:
                md5_hash.update(read_bytes)
    return md5_hash.hexdigest()

def content_has_changed(filenames, md5):
    return md5 != compute_hash(filenames)

def image_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)


def thumb_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)


def medium_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model May be used in a
    model.save() method."""
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old
