from colorlog import ColoredFormatter

from .abstract_base import *

DEBUG = True

# NOTE: Can be removed once Django 3 is used
ALLOWED_HOSTS = [
    '.localhost',
    '127.0.0.1',
    '[::1]'
]

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'zds.middlewares.nocacheindevmiddleware.NoCacheInDevMiddleware',
) + MIDDLEWARE

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            '()': ColoredFormatter,
            'format': '%(log_color)s %(levelname)s %(reset)s %(bold_black)s%(name)s%(reset)s %(message)s',
            'log_colors': {
                'DEBUG': 'fg_white,bg_black',
                'INFO': 'fg_black,bg_bold_white',
                'WARNING': 'fg_black,bg_bold_yellow',
                'ERROR': 'fg_bold_white,bg_bold_red',
                'CRITICAL': 'fg_bold_white,bg_bold_red',
            },
        },

        'django.server': {
            '()': ColoredFormatter,
            'format': '%(log_color)s%(message)s',
            'log_colors': {
                'INFO': 'bold_black',
                'WARNING': 'bold_yellow',
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_red',
            },
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },

        'django.server': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },

    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['console'],
        },

        'django.server': {
            'level': 'INFO',
            'handlers': ['django.server'],
            'propagate': False,
        },

        'zds': {
            'level': 'DEBUG',  # Important because the default level is 'WARNING' or something like that
            'handlers': ['console'],
        },
    },
}

ZDS_APP['site']['url'] = 'http://127.0.0.1:8000'
ZDS_APP['site']['dns'] = '127.0.0.1:8000'

ZDS_APP['very_top_banner'] = {
    'background_color': '#666',
    'border_color': '#353535',
    'color': 'white',
    'message': 'Version locale',
    'slug': 'version-locale'
}
