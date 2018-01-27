from .abstract_base import *
from .abstract_test import *
import logging

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zds_test',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': 'SET sql_mode=\'STRICT_TRANS_TABLES\'',
        },
    }
}

LOGGING['handlers']['console']['level'] = 'ERROR'
LOGGING['disable_existing_loggers'] = False

logger = logging.getLogger('console')
logger.setLevel(logging.ERROR)
