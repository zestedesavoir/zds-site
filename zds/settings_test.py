DEBUG = False
TEMPLATE_DEBUG = False

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(name)s %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },

        'django.request': {
            'level': 'ERROR',
            'handlers': [],
            'propagate': False,
        },

        'zds': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
}
