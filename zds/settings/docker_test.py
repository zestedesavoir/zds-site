from .test import *
from .docker import *

# Unlike settings_docker_test.py, we don't change the database
# location here.  We don't care if the database file is outside of the
# volume, we don't care about persistence.

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    }
}

ZDS_APP['site']['secure_url'] = u'http://127.0.0.1:8000'
