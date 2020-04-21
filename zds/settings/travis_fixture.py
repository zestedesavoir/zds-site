from .ci_test import *

LOGGING['loggers']['zds.utils.templatetags.emarkdown'] = {
    'level': 'INFO',
    'handlers': ['console'],
}
