# coding: utf-8

"""
Django settings for zestedesavoir project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os

from django.contrib.messages import constants as message_constants


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n!01nl+318#x75_%le8#s0=-*ysw&amp;y49uc#t=*wvi(9hnyii0z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

ADMINS = (
    ('user', 'mail'),
)

MANAGERS = ADMINS

SITE_ID = 1


# Application definition

INSTALLED_APPS = (
    # Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    # Third apps
    'easy_thumbnails',
    'easy_thumbnails.optimize',
    'south',
    'crispy_forms',
    'email_obfuscator',
    'haystack',
    'munin',

    # ZDS apps
    # Apps DB tables are created in THIS order by default
    # --> Order is CRITICAL to properly handle foreign keys
    'zds.utils',
    'zds.pages',
    'zds.gallery',
    'zds.mp',
    'zds.article',
    'zds.forum',
    'zds.tutorial',
    'zds.member',

    # Django admin app
    'django.contrib.admin',

)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'zds.utils.ThreadLocals',
    'zds.middlewares.SetLastVisitMiddleware.SetLastVisitMiddleware',
    'zds.middlewares.profile.ProfileMiddleware',
)

ROOT_URLCONF = 'zds.urls'

WSGI_APPLICATION = 'zds.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'base.db'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = False

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'dist'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

# Django fileserve settings (set to True for local dev version only)

SERVE = False


# Media files (uploaded files)
# https://docs.djangoproject.com/en/1.6/howto/static-files/#serving-files-uploaded-by-a-user-during-development

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'


# Templates
# https://docs.djangoproject.com/en/1.6/topics/templates/

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates')
]


# Logging
# https://docs.djangoproject.com/en/1.6/topics/logging/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Cache
# https://docs.djangoproject.com/en/1.6/topics/cache/

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


# Auth, sessions and login

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

AUTH_PROFILE_MODULE = 'member.Profile'

LOGIN_URL = '/membres/connexion'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: '/membres/voir/{0}/'.format(u.username.encode('utf-8'))
}


# Messages

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'alert',
}


# GeoIP
# https://django-geoip.readthedocs.org/en/latest/

GEOIP_PATH = os.path.join(BASE_DIR, 'geodata')


# django-crispy-forms
# http://django-crispy-forms.readthedocs.org/en/latest/

CRISPY_TEMPLATE_PACK = 'bootstrap'


# South (migrations)
# https://south.readthedocs.org/en/latest/

SOUTH_MIGRATION_MODULES = {
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}


# Easy Thumbnails
# http://easy-thumbnails.readthedocs.org/en/latest/

THUMBNAIL_ALIASES = {
    '': {
        'avatar': {'size': (60, 60), 'crop': True},
        'avatar_mini': {'size': (24, 24), 'crop': True},
        'tutorial_illu': {'size': (60, 60), 'crop': True},
        'article_illu': {'size': (60, 60), 'crop': True},
        'gallery': {'size': (120, 120), 'crop': True},
        'content': {'size': (960, 960), 'crop': False},
    },
}


# Pandoc
# https://github.com/bebraw/pypandoc

PANDOC_LOC = ''

PANDOC_LOG = './pandoc.log'

PANDOC_LOG_STATE = False


# Haystack
# http://django-haystack.readthedocs.org/en/latest/

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr'
        # ...or for multicore...
        # 'URL': 'http://127.0.0.1:8983/solr/mysite',
    },
}


# Load the ZDS settings

from settings_zds import *


# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *
except ImportError:
    pass
