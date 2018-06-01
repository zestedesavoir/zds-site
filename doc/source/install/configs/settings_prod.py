# coding: utf-8

# Zeste de Savoir settings file for production
# WARNING: this file MUST be secret !!

import os

from raven import Client
from zds.utils.context_processor import get_git_version

from settings import ABSOLUTE_URL_OVERRIDES, AUTHENTICATION_BACKENDS, BASE_DIR
from settings import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, CORS_EXPOSE_HEADERS
from settings import CORS_ORIGIN_ALLOW_ALL, CRISPY_TEMPLATE_PACK, FILE_UPLOAD_HANDLERS
from settings import GEOIP_PATH
from settings import INSTALLED_APPS, LANGUAGES, LANGUAGE_CODE, LOCALE_PATHS
from settings import LOGIN_REDIRECT_URL, LOGIN_URL, MEDIA_URL, MESSAGE_TAGS
from settings import MIDDLEWARE_CLASSES, OAUTH2_PROVIDER, REST_FRAMEWORK
from settings import REST_FRAMEWORK_EXTENSIONS, ROOT_URLCONF, SERVE, SITE_ID
from settings import STATICFILES_DIRS, STATICFILES_FINDERS, STATIC_URL, SWAGGER_SETTINGS
from settings import THUMBNAIL_ALIASES, THUMBNAIL_PRESERVE_EXTENSIONS, THUMBNAIL_QUALITY
from settings import TIME_ZONE, USE_I18N, USE_TZ, WSGI_APPLICATION, ZDS_APP
from settings import ES_ENABLED, ES_CONNECTIONS, ES_SEARCH_INDEX

##### Django settings #####

# NEVER set this True !!
DEBUG = False

USE_L10N = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zdsdb',
        'USER': 'zds',
        'PASSWORD': 'to-fill',  # KEEP THIS SECRET !!
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# KEEP THIS SECRET !!
SECRET_KEY = 'to-fill'

INSTALLED_APPS += (
    # Sentry client (errors logs)
    'raven.contrib.django.raven_compat',
)

ALLOWED_HOSTS = [
    'zdsappserver',
    'gandi.zestedesavoir.com',
    'gandi.zestedesavoir.com.',
    '.zestedesavoir.com',
    '.zestedesavoir.com.',
    '127.0.0.1',
    'localhost',
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = False
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
#EMAIL_HOST_USER = 'site@zestedesavoir.com'
#EMAIL_HOST_PASSWORD = 'to-fill'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 4

MEDIA_ROOT = '/opt/zds/data/media'

STATIC_ROOT = '/opt/zds/data/static'
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.CachedStaticFilesStorage"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                # Default context processors
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
                # ZDS context processors
                'zds.utils.context_processor.app_settings',
                'zds.utils.context_processor.git_version',
            ],
            'debug': DEBUG,
        }
    },
]

# Sentry (+ raven, the Python Client)
# https://docs.getsentry.com/hosted/clients/python/integrations/django/
RAVEN_CONFIG = {
    'dsn': 'to-fill',
    'release': get_git_version()['name'],
}

LOGGING = {
   'version': 1,
   'disable_existing_loggers': True,
   'formatters': {
       'verbose': {
           'format': '[%(levelname)s] -- %(asctime)s -- %(module)s : %(message)s'
       },
       'simple': {
           'format': '[%(levelname)s] %(message)s'
       },
   },
   'handlers': {
        'django_log':{
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/zds/logging.django.log',
            'formatter': 'verbose'
        },
        'debug_log':{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/zds/debug.django.log',
            'formatter': 'verbose'
        },
        'generator_log':{
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/zds/generator.log',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
       'sentry': {
            'level': 'ERROR',  # For beta purpose it can be lowered to WARNING
            'class': 'raven.handlers.logging.SentryHandler',
            'dsn': 'to-fill'
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
            'level': 'WARNING',
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

# https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')


##### Dependencies settings #####


# easy-thumbnails
# http://easy-thumbnails.readthedocs.io/en/2.1/ref/settings/
THUMBNAIL_OPTIMIZE_COMMAND = {
    'png': '/usr/bin/optipng {filename}',
    'gif': '/usr/bin/optipng {filename}',
    'jpeg': '/usr/bin/jpegoptim {filename}'
}

# Pandoc settings
PANDOC_LOC = '/usr/local/bin/'
PANDOC_LOG = '/var/log/zds/pandoc.log'
PANDOC_LOG_STATE = True
# fix for Gandi
PANDOC_PDF_PARAM = ("--latex-engine=xelatex "
                    "--template={} -s -S -N "
                    "--toc -V documentclass=scrbook -V lang=francais "
                    "-V mainfont=Merriweather -V monofont=\"SourceCodePro-Regular\" "
                    "-V fontsize=12pt -V geometry:margin=1in ".format('/opt/zds/zds-site/assets/tex/template.tex'))

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
# KEEP THIS SECRET !!
SOCIAL_AUTH_ACEBOOK_KEY = 'to-fill'
SOCIAL_AUTH_ACEBOOK_SECRET = 'to-fill'
SOCIAL_AUTH_WITTER_KEY = 'to-fill'
SOCIAL_AUTH_WITTER_SECRET = 'to-fill'
SOCIAL_AUTH_OOGLE_OAUTH2_KEY = 'to-fill'
SOCIAL_AUTH_OOGLE_OAUTH2_SECRET = 'to-fill'
SOCIAL_AUTH_ANITIZE_REDIRECTS = 'to-fill'

# Django reCAPTCHA
# https://github.com/praekelt/django-recaptcha
USE_CAPTCHA = False
NOCAPTCHA = True   # Use the "No Captcha engine"
RECAPTCHA_USE_SSL = True
# KEEP THIS SECRET !!
RECAPTCHA_UBLIC_KEY = 'to-fill'
RECAPTCHA_RIVATE_KEY = 'to-fill'


##### ZdS settings #####

# added in v20
ZDS_APP['site']['secure_url'] = 'https://zestedesavoir.com'

# added in v21
ZDS_APP['display_search_bar'] = True

# forum
ZDS_APP['forum']['beta_forum_id'] = 23

# member
ZDS_APP['member']['anonymous_account'] = 'anonyme'
ZDS_APP['member']['external_account'] = 'Auteur externe'
ZDS_APP['member']['bot_account'] = 'Clem'

# site
ZDS_APP['site']['url'] = 'https://zestedesavoir.com'
ZDS_APP['site']['association']['email'] = 'communication@zestedesavoir.com'
ZDS_APP['site']['association']['fee'] = u'(montant en attente de procédures administratives)'
ZDS_APP['site']['googleAnalyticsID'] = 'to-fill'
ZDS_APP['site']['googleTagManagerID'] = 'to-fill'

# content
#ZDS_APP['content']['build_pdf_when_published'] = False
ZDS_APP['article']['repo_path'] = '/opt/zds/data/articles-data'
ZDS_APP['content']['repo_private_path'] = '/opt/zds/data/contents-private'
ZDS_APP['content']['repo_public_path'] = '/opt/zds/data/contents-public'
ZDS_APP['content']['extra_content_generation_policy'] = 'WATCHDOG'

# enable ping!
ZDS_APP['comment']['enable_pings'] = False

# Vote anonymisation - cf v18 : https://goo.gl/L6X4hw
VOTES_ID_LIMIT = 131319

# tags in menu
TOP_TAG_MAX = 5

# path for old tutorials for Site du Z&ro
SDZ_TUTO_DIR = '/home/zds/tutos_sdzv3/Sources_md'

# Force HTTPS for logged users
FORCE_HTTPS_FOR_MEMBERS = True
ENABLE_HTTPS_DECORATOR = True

# visual changes
#ZDS_APP['visual_changes'] = ['snow', 'clem-christmas']
#ZDS_APP['visual_changes'] = ['clem-halloween']

ES_SEARCH_INDEX['shards'] = 3
