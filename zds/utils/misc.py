import hashlib
import re

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


def convert_camel_to_underscore(camel_case):
    """
    Converts a name in camel case to underscore.
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def contains_utf8mb4(s):
    """
    This string contains at least one character of more than 3 bytes
    """
    if not isinstance(s, str):
        s = str(s, 'utf-8')
    re_pattern = re.compile('[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    return s != re_pattern.sub('\uFFFD', s)
