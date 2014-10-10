# coding: utf-8

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
# INTERNAL_IPS = ('127.0.0.1',)  # debug toolbar


ADMINS = (
    ('user', 'mail'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'base.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

SITE_ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'dist'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

FIXTURE_DIRS = (os.path.join(SITE_ROOT, 'fixtures'))

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n!01nl+318#x75_%le8#s0=-*ysw&amp;y49uc#t=*wvi(9hnyii0z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'zds.utils.ThreadLocals',
    'zds.middlewares.SetLastVisitMiddleware.SetLastVisitMiddleware',
    'zds.middlewares.profile.ProfileMiddleware',
)

ROOT_URLCONF = 'zds.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'zds.wsgi.application'

TEMPLATE_DIRS = [
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates')
]

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default context processors
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages'
)

CRISPY_TEMPLATE_PACK = 'bootstrap'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    'easy_thumbnails',
    'easy_thumbnails.optimize',
    'south',
    'crispy_forms',
    'email_obfuscator',
    'haystack',
    'munin',

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
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SOUTH_MIGRATION_MODULES = {
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}

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

if (DEBUG):
    INSTALLED_APPS += (
        'debug_toolbar',
    )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

AUTH_PROFILE_MODULE = 'member.Profile'
LOGIN_URL = '/membres/connexion'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: '/membres/voir/{0}/'.format(u.username.encode('utf-8'))
}


# Django fileserve settings (set to True for local dev version only)
SERVE = False

PANDOC_LOC = ''
# LOG PATH FOR PANDOC LOGGING
PANDOC_LOG = './pandoc.log'
PANDOC_LOG_STATE = False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr'
        # ...or for multicore...
        # 'URL': 'http://127.0.0.1:8983/solr/mysite',
    },
}

GEOIP_PATH = os.path.join(SITE_ROOT, 'geodata')

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'alert',
}

SDZ_TUTO_DIR = ''

ZDS_APP = {
    'site': {
        'name': u"ZesteDeSavoir",
        'litteral_name': u"Zeste de Savoir",
        'slogan': u"Zeste de Savoir, la connaissance pour tous et sans pépins",
        'abbr': u"zds",
        'url': u"http://127.0.0.1:8000",
        'dns': u"zestedesavoir.com",
        'email_contact': u"communication@zestedesavoir.com",
        'email_noreply': u"noreply@zestedesavoir.com",
        'repository': u"https://github.com/zestedesavoir/zds-site",
        'short_description': u"",
        'long_description': u"Zeste de Savoir est un site de partage de connaissances "
                            u"sur lequel vous trouverez des tutoriels de tous niveaux, "
                            u"des articles et des forums d'entraide animés par et pour "
                            u"la communauté.",
        'year': u"2014",
        'association': {
            'name': u"Zeste de Savoir",
            'fee': u"30 €",
            'email': u"association@zestedesavoir.com",
            'email_ca': u"ca-zeste-de-savoir@googlegroups.com"
        },
        'licenses': {
            'logo': {
                'code': u"CC-BY",
                'title': u"Creative Commons License",
                'description': u"Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - Partage dans les Mêmes Conditions 4.0 International.",
                'url_image': u"http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                'url_license': u"http://creativecommons.org/licenses/by-nc-sa/4.0/",
                'author': u"MaxRoyo"
            },
            'cookies': {
                'code': u"CC-BY",
                'title': u"Licence Creative Commons",
                'description': u"licence Creative Commons Attribution 4.0 International",
                'url_image': u"http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                'url_license': u"http://creativecommons.org/licenses/by-nc-sa/4.0/"
            },
            'source': {
                'code' : u"GPL v3",
                'url_license': u"http://www.gnu.org/licenses/gpl-3.0.html",
                'provider_name': u"Progdupeupl",
                'provider_url': u"http://progdupeu.pl",
            }
        },
        'hosting': {
            'name': u"OVH",
            'address': u"2 rue Kellermann - 59100 Roubaix - France"
        },
        'cnil': u"1771020",
    },
    'member': {
        'bot_account': u"admin",
        'anonymous_account': u"anonymous",
        'external_account': u"external",
        'members_per_page': 100,
    },
    'gallery': {
        'image_max_size': 1024 * 1024,
    },
    'article': {
        'repo_path': os.path.join(SITE_ROOT, 'articles-data'),
    },
    'tutorial': {
        'repo_path': os.path.join(SITE_ROOT, 'tutoriels-private'),
        'repo_public_path': os.path.join(SITE_ROOT, 'tutoriels-public'),
        'default_license_pk': 7
    },
    'forum': {
        'posts_per_page': 21,
        'topics_per_page': 21,
        'spam_limit_seconds': 60 * 15,
        'spam_limit_participant': 2,
        'followed_topics_per_page': 21,
        'beta_forum_id': 1,
        'max_post_length': 1000000,
        'top_tag_max': 5,
    }
}

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *
except ImportError:
    pass
