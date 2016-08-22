from zds.settings import *
from zds.settings_test import *


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    }
}

ZDS_APP['site']['secure_url'] = u'http://127.0.0.1:8000'
