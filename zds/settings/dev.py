from colorlog import ColoredFormatter

from .abstract_base import *

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES


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
