from os.path import join

from django.contrib.messages import constants as message_constants
from django.utils.http import urlquote
from django.utils.translation import gettext_lazy as _

from .config import config
from .base_dir import BASE_DIR


INTERNAL_IPS = ('127.0.0.1',)  # debug toolbar

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(BASE_DIR, 'base.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': ''
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

LOCALE_PATHS = (
    join(BASE_DIR, 'conf/locale/'),
)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

LANGUAGES = (
    ('fr', _('Français')),
    ('en', _('Anglais')),
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/home/media/media.lawrence.com/media/'
MEDIA_ROOT = join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://media.lawrence.com/media/', 'http://example.com/media/'
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' 'static/' subdirectories and in STATICFILES_DIRS.
# Example: '/home/media/media.lawrence.com/static/'
STATIC_ROOT = join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: 'http://media.lawrence.com/static/'
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(BASE_DIR, 'dist'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('secret_key', 'n!01nl+318#x75_%le8#s0=-*ysw&amp;y49uc#t=*wvi(9hnyii0z')

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

MIDDLEWARE_CLASSES = (
    # CorsMiddleware needs to be before CommonMiddleware.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'zds.utils.ThreadLocals',
    'zds.middlewares.setlastvisitmiddleware.SetLastVisitMiddleware',
    'zds.member.utils.ZDSCustomizeSocialAuthExceptionMiddleware',
)

ROOT_URLCONF = 'zds.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'zds.wsgi.application'

django_template_engine = {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'DIRS': [
        join(BASE_DIR, 'templates'),
    ],
    'OPTIONS': {
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
            'zds.utils.context_processor.version',
        ],
    },
}

TEMPLATES = [django_template_engine]

CRISPY_TEMPLATE_PACK = 'bootstrap'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    'easy_thumbnails',
    'easy_thumbnails.optimize',
    'crispy_forms',
    'munin',
    'social.apps.django_app.default',
    'rest_framework',
    'rest_framework_swagger',
    'dry_rest_permissions',
    'corsheaders',
    'oauth2_provider',
    'captcha',

    # Apps DB tables are created in THIS order by default
    # --> Order is CRITICAL to properly handle foreign keys
    'zds.utils',
    'zds.pages',
    'zds.gallery',
    'zds.mp',
    'zds.forum',
    'zds.tutorialv2',
    'zds.member',
    'zds.featured',
    'zds.searchv2',
    'zds.notification',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'zds.api.pagination.DefaultPagination',
    # Active OAuth2 authentication.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        # 'rest_framework.parsers.XMLParser',
        'rest_framework_xml.parsers.XMLParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.XMLRenderer',
        'rest_framework_xml.renderers.XMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '2000/hour'
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

REST_FRAMEWORK_EXTENSIONS = {
    # If the cache isn't specify in the API, the time of the cache
    # is specified here in seconds.
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
}


SWAGGER_SETTINGS = {
    'APIS_SORTER': 'alpha',
    'OPERATIONS_SORTER': 'alpha',
    'SHOW_REQUEST_HEADERS': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
    ],
}

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_METHODS = (
    'GET',
    'POST',
    'PUT',
    'DELETE',
)

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'x-data-format'
)

CORS_EXPOSE_HEADERS = (
    'etag',
    'link'
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

        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

LOGIN_URL = 'member-login'
LOGIN_REDIRECT_URL = '/'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: '/membres/voir/{0}/'.format(urlquote(u.username.encode('utf-8')))
}

# Django fileserve settings (set to True for local dev version only)
SERVE = False

# Fake mails (in console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'alert',
}

AUTHENTICATION_BACKENDS = ('social.backends.facebook.FacebookOAuth2',
                           'social.backends.google.GoogleOAuth2',
                           'django.contrib.auth.backends.ModelBackend')

# To remove a useless warning in Django 1.7.
# See http://daniel.hepper.net/blog/2014/04/fixing-1_6-w001-when-upgrading-from-django-1-5-to-1-7/
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Properly handle HTTPS vs HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
