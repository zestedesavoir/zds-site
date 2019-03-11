from .dev import *

LOGGING['loggers']['zds.utils.templatetags.emarkdown'] = {
    'loggers': {
        'zds': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    },
}
