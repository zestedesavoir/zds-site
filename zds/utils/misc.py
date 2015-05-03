# coding: utf-8
import hashlib

THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80

MEDIUM_MAX_WIDTH = 200
MEDIUM_MAX_HEIGHT = 200


def compute_hash(filenames):
    """returns a md5 hexdigest of group of files to check if they have change"""
    md5_hash = hashlib.md5()
    for filename in filenames:
        if filename:
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


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model May be used in a
    model.save() method."""
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old
