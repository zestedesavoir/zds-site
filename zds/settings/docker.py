import os
from os.path import join

from .dev import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zdsdb',
        'USER': 'zds',
        'PASSWORD': 'zds',
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
}

allowed_hosts_string = os.environ.get('ZDS_ALLOWED_HOSTS')
if allowed_hosts_string:
    ALLOWED_HOSTS = allowed_hosts_string.split(',')

ZDS_APP['article']['repo_path'] = join(BASE_DIR, 'articles-data')

ZDS_APP['opinions']['repo_path'] = join(BASE_DIR, 'opinions-data')

ZDS_APP['tutorial']['repo_path'] = join(BASE_DIR, 'tutoriels-private')
ZDS_APP['tutorial']['repo_public_path'] = join(BASE_DIR, 'tutoriels-public')

ZDS_APP['content']['repo_private_path'] = join(BASE_DIR, 'contents-private')
ZDS_APP['content']['repo_public_path'] = join(BASE_DIR, 'contents-public')

# No need to set 'extra_content_watchdog_dir' since
# 'extra_content_generation_policy' is 'SYNC' by default.


ES_CONNECTIONS['default']['hosts'] = 'elasticsearch:9200'
ZDS_APP['site']['secure_url'] = 'http://127.0.0.1:8000'
ZDS_APP['zmd']['server'] = 'http://zmarkdown:27272'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    }
}
