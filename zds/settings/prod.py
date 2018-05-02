from .abstract_base import *

# For secrets, prefer `config[key]` over `config.get(key)` in this
# file because we really want to raise an error if a secret is not
# defined.


###############################################################################
# DJANGO SETTINGS


DEBUG = False

USE_L10N = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config['databases']['default'].get('name', 'zdsdb'),
        'USER': config['databases']['default'].get('user', 'zds'),
        'PASSWORD': config['databases']['default']['password'],
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
}

INSTALLED_APPS += (
    # Sentry client (errors reporting)
    'raven.contrib.django.raven_compat',
)

ALLOWED_HOSTS = [
    'beta.zestedesavoir.com',
    'scaleway.zestedesavoir.com',
    'zdsappserver',
    'gandi.zestedesavoir.com',
    'gandi.zestedesavoir.com.',
    '.zestedesavoir.com',
    '.zestedesavoir.com.',
    '127.0.0.1',
    'localhost',
    '163.172.171.246',
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = False
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 4

MEDIA_ROOT = '/opt/zds/data/media'

STATIC_ROOT = '/opt/zds/data/static'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

django_template_engine['APP_DIRS'] = False
django_template_engine['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]


def _get_version():
    from zds import __version__, git_version
    if git_version is None:
        return __version__
    else:
        return '{0}/{1}'.format(__version__, git_version[:7])


# Sentry (+ raven, the Python Client)
# https://docs.getsentry.com/hosted/clients/python/integrations/django/
RAVEN_CONFIG = {
    'dsn': config['raven']['dsn'],
    'release': _get_version(),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] -- %(asctime)s -- %(name)s : %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },

    'handlers': {
        'django_log': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 10,  # rotate when it reaches 10 MB
            'backupCount': 50,  # only keep the last 50 rotated files, 10M*50 -> 500M
            'filename': '/var/log/zds/logging.django.log',
            'formatter': 'verbose'
        },
        'debug_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 10,  # rotate when it reaches 10 MB
            'backupCount': 50,  # only keep the last 50 rotated files, 10M*50 -> 500M
            'filename': '/var/log/zds/debug.django.log',
            'formatter': 'verbose'
        },
        'generator_log': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 10,  # rotate when it reaches 10 MB
            'backupCount': 50,  # only keep the last 50 rotated files, 10M*50 -> 500M
            'filename': '/var/log/zds/generator.log',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'sentry': {
            'level': 'WARNING',  # For beta purpose it can be lowered to WARNING
            'class': 'raven.handlers.logging.SentryHandler',
            'dsn': RAVEN_CONFIG['dsn'],
        },
    },

    'loggers': {
        'django': {
            'handlers': ['django_log'],
            'propagate': True,
            'level': 'WARNING',
        },
        'zds': {
            'handlers': ['django_log', 'sentry'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins', 'django_log'],
            'level': 'ERROR',
            'propagate': False,
        },
        'generator': {
            'handlers': ['generator_log'],
            'level': 'WARNING',
        }
    }
}


###############################################################################
# REQUIREMENTS SETTINGS


# easy-thumbnails
# http://easy-thumbnails.readthedocs.io/en/2.1/ref/optimize/
THUMBNAIL_OPTIMIZE_COMMAND = {
    'png': '/usr/bin/optipng {filename}',
    'gif': '/usr/bin/optipng {filename}',
    'jpeg': '/usr/bin/jpegoptim {filename}'
}


# python-social-auth
# http://psa.matiasaguirre.net/docs/configuration/django.html
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.create_user',
    'zds.member.models.save_profile',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)


###############################################################################
# ZESTE DE SAVOIR SETTINGS


ES_SEARCH_INDEX['shards'] = config['elasticsearch'].get('shards', 3)


ZDS_APP['site']['association']['email'] = 'communication@zestedesavoir.com'

# content
# ZDS_APP['content']['build_pdf_when_published'] = False
ZDS_APP['article']['repo_path'] = '/opt/zds/data/articles-data'
ZDS_APP['content']['repo_private_path'] = '/opt/zds/data/contents-private'
ZDS_APP['content']['repo_public_path'] = '/opt/zds/data/contents-public'
ZDS_APP['content']['extra_content_generation_policy'] = 'WATCHDOG'

# allow to mention (and notify) members in messages
# still a beta feature, keep it disabled for the time being
ZDS_APP['comment']['enable_pings'] = False

ZDS_APP['visual_changes'] = zds_config.get('visual_changes', [])
