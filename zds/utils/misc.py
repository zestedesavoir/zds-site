import hashlib
import re

from django.contrib.auth import get_user_model
from django.http import HttpRequest

THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80

MEDIUM_MAX_WIDTH = 200
MEDIUM_MAX_HEIGHT = 200


def compute_hash(filenames):
    """returns a md5 hexdigest of group of files to check if they have change"""
    md5_hash = hashlib.md5()
    for filename in filenames:
        if filename:
            file_handle = open(filename, "rb")
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


def has_changed(instance, field, manager="objects"):
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
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_case)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def remove_utf8mb4(s):
    """
    Remove characters of more than 3 bytes.
    """
    if not isinstance(s, str):
        s = str(s, "utf-8")
    re_pattern = re.compile("[^\u0000-\uD7FF\uE000-\uFFFF]", re.UNICODE)
    return re_pattern.sub("", s)


def contains_utf8mb4(s):
    """
    Check if this string contains at least one character of more than 3 bytes.
    """
    return s != remove_utf8mb4(s)


def check_essential_accounts():
    """
    Verify that essential accounts are present in the database.
    Raise an exception if it is not the case.
    """

    from django.conf import settings

    User = get_user_model()
    essential_accounts = ("bot_account", "anonymous_account", "external_account")

    for account in essential_accounts:
        username = settings.ZDS_APP["member"][account]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise Exception(
                f"User {username!r} does not exist. You must create it to run the server. "
                f"On a development instance, load the fixtures to solve this issue."
            )


def is_ajax(request: HttpRequest):
    """
    Check whether the request was sent asynchronously.

    The function returns True for :

    * requests sent using jQuery.ajax() since it sets the header `X-Requested-With`
      to `XMLHttpRequest` by default ;
    * requests sent using the tools provided by `ajax.js`, which reproduce the behavior
      described above to ease the progressive removal of jQuery from the codebase.

    The function returns False for requests without the appropriate header.
    These requests will not be recognized as AJAX.

    The function replaces `request.is_ajax()`, which is removed starting from Django 4.0.
    """
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
