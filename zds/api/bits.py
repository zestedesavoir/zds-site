# -*- coding: utf-8 -*-
import datetime
from django.core.cache import cache
from django.utils.encoding import force_text
from rest_framework_extensions.key_constructor.bits import QueryParamsKeyBit, KeyBitBase


class UpdatedAtKeyBit(KeyBitBase):
    """
    A custom key to allow invalidation of a cache.

    See official documentation to know more about the usage of this class:
    http://chibisov.github.io/drf-extensions/docs/#custom-key-bit
    """
    update_key = None

    def __init__(self, update_key, params=None):
        super(UpdatedAtKeyBit, self).__init__(params)
        self.update_key = update_key

    def get_data(self, **kwargs):
        value = cache.get(self.update_key)
        if value is None:
            value = datetime.datetime.utcnow()
            cache.set(self.update_key, value=value)
        return force_text(value)
