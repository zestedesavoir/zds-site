# coding: utf-8

import os
import sys

from django.contrib.messages import constants as message_constants
from django.utils.http import urlquote
from django.utils.translation import gettext_lazy as _

# Changes the default encoding of python to UTF-8.
# Theses instructions don't change encoding python outside Zeste de Savoir.
reload(sys)
sys.setdefaultencoding('UTF8')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
# INTERNAL_IPS = ('127.0.0.1',)  # debug toolbar

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'base.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'timeout': 20  # SQLite doesn't currently handle concurency well. This will increase the default timeout
                           # value. This will simply make SQLite wait a bit longer before throwing “database is locked”
                           # errors. it won’t really do anything to solve them.
        }
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
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'dist'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'))

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n!01nl+318#x75_%le8#s0=-*ysw&amp;y49uc#t=*wvi(9hnyii0z' # noqa

FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
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
    os.path.join(BASE_DIR, 'templates')
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
    'django.contrib.messages.context_processors.messages',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    # ZDS context processors
    'zds.utils.context_processor.app_settings',
    'zds.utils.context_processor.git_version',
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
    'crispy_forms',
    'haystack',
    'munin',
    'social.apps.django_app.default',
    'rest_framework',
    'rest_framework_swagger',
    'corsheaders',
    'oauth2_provider',

    # Apps DB tables are created in THIS order by default
    # --> Order is CRITICAL to properly handle foreign keys
    'zds.utils',
    'zds.pages',
    'zds.gallery',
    'zds.mp',
    'zds.article',
    
    'zds.forum',
    'zds.tutorial',
    'zds.tutorialv2',
    'zds.member',
    'zds.featured',
    'zds.search',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SITE_ID = 1

THUMBNAIL_ALIASES = {
    '': {
        'avatar': {'size': (60, 60), 'crop': True},
        'avatar_mini': {'size': (24, 24), 'crop': True},
        'tutorial_illu': {'size': (60, 60), 'crop': True},
        'article_illu': {'size': (60, 60), 'crop': True},
        'content_thumb': {'size': (96, 96), 'crop': True},
        'help_illu': {'size': (48, 48), 'crop': True},
        'help_mini_illu': {'size': (26, 26), 'crop': True},
        'gallery': {'size': (120, 120), 'crop': True},
        'content': {'size': (960, 960), 'crop': False},
    },
}

REST_FRAMEWORK = {
    # If the pagination isn't specify in the API, its configuration is
    # specified here.
    'PAGINATE_BY': 10,                 # Default to 10
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100,             # Maximum limit allowed when using `?page_size=xxx`.
    # Active OAuth2 authentication.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        #'rest_framework.parsers.XMLParser',
        'rest_framework_xml.parsers.XMLParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        #'rest_framework.renderers.XMLRenderer',
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
    }
}

REST_FRAMEWORK_EXTENSIONS = {
    # If the cache isn't specify in the API, the time of the cache
    # is specified here in seconds.
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
}

SWAGGER_SETTINGS = {
    'enabled_methods': [
        'get',
        'post',
        'put',
        'delete'
    ]
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

if DEBUG:
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

LOGIN_URL = '/membres/connexion'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: '/membres/voir/{0}/'.format(urlquote(u.username.encode('utf-8')))
}


# Django fileserve settings (set to True for local dev version only)
SERVE = False

PANDOC_LOC = ''
PANDOC_PDF_PARAM = ("--latex-engine=xelatex "
                    "--template=../../../assets/tex/template.tex -s -S -N "
                    "--toc -V documentclass=scrbook -V lang=francais "
                    "-V mainfont=Merriweather -V monofont=\"Andale Mono\" "
                    "-V fontsize=12pt -V geometry:margin=1in ")
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
HAYSTACK_CUSTOM_HIGHLIGHTER = 'zds.utils.highlighter.SearchHighlighter'

GEOIP_PATH = os.path.join(BASE_DIR, 'geodata')

# Fake mails (in console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'alert',
}

SDZ_TUTO_DIR = ''

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'conf/locale/'),
)

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
        'bugtracker': u"https://github.com/zestedesavoir/zds-site/issues",
        'forum_feedback_users': u"/forums/communaute/bug-suggestions/",
        'contribute_link': u"https://github.com/zestedesavoir/zds-site/blob/dev/CONTRIBUTING.md",
        'short_description': u"",
        'long_description': u"Zeste de Savoir est un site de partage de connaissances "
                            u"sur lequel vous trouverez des tutoriels de tous niveaux, "
                            u"des articles et des forums d'entraide animés par et pour "
                            u"la communauté.",
        'association': {
            'name': u"Zeste de Savoir",
            'fee': u"20 €",
            'email': u"association@zestedesavoir.com",
            'email_ca': u"ca-zeste-de-savoir@googlegroups.com"
        },
        'licenses': {
            'logo': {
                'code': u"CC-BY",
                'title': u"Creative Commons License",
                'description': u"Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - "
                               u"Partage dans les Mêmes Conditions 4.0 International.",
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
                'code': u"GPL v3",
                'url_license': u"http://www.gnu.org/licenses/gpl-3.0.html",
                'provider_name': u"Progdupeupl",
                'provider_url': u"http://pdp.microjoe.org",
            },
            'licence_info_title': u'http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-lic'
                                  u'ences-sur-zeste-de-savoir/',
            'licence_info_link': u'Le droit d\'auteur, Creative Commons et les licences sur Zeste de Savoir'
        },
        'hosting': {
            'name': u"OVH",
            'address': u"2 rue Kellermann - 59100 Roubaix - France"
        },
        'social': {
            'facebook': u'https://www.facebook.com/ZesteDeSavoir',
            'twitter': u'https://twitter.com/ZesteDeSavoir',
            'googleplus': u'https://plus.google.com/u/0/107033688356682807298'
        },
        'cnil': u"1771020",
    },
    'member': {
        'bot_account': u"admin",
        'anonymous_account': u"anonymous",
        'external_account': u"external",
        'bot_group': u'bot',
        'members_per_page': 100,
    },
    'gallery': {
        'image_max_size': 1024 * 1024,
    },
    'article': {
        'home_number': 4,
        'repo_path': os.path.join(BASE_DIR, 'articles-data')
    },
    'tutorial': {
        'repo_path': os.path.join(BASE_DIR, 'tutoriels-private'),
        'repo_public_path': os.path.join(BASE_DIR, 'tutoriels-public'),
        'default_license_pk': 7,
        'home_number': 5,
        'helps_per_page': 20,
        'content_per_page': 50,
        'feed_length': 5
    },
    'content': {
        'repo_private_path': os.path.join(BASE_DIR, 'contents-private'),
        'repo_public_path': os.path.join(BASE_DIR, 'contents-public'),
        'extra_contents_dirname': 'extra_contents',
        'max_tree_depth': 3,
        'default_license_pk': 7,
        'content_per_page': 50,
        'notes_per_page': 25,
        'helps_per_page': 20,
        'feed_length': 5,
        'user_page_number': 5,
        'default_image': os.path.join(BASE_DIR, "fixtures", "noir_black.png"),
        'import_image_prefix': 'archive',
        'build_pdf_when_published': True
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
        'home_number': 5,
        'old_post_limit_days': 90
    },
    'topic': {
        'home_number': 6,
    },
    'featured_resource': {
        'featured_per_page': 100,
        'home_number': 5,
    },
    'paginator': {
        'folding_limit': 4
    }
}

LOGIN_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = ('social.backends.facebook.FacebookOAuth2',
                           'social.backends.google.GoogleOAuth2',
                           'django.contrib.auth.backends.ModelBackend')
SOCIAL_AUTH_GOOGLE_OAUTH2_USE_DEPRECATED_API = True
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'zds.member.models.save_profile',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)

# redefine for real key and secret code
SOCIAL_AUTH_FACEBOOK_KEY = ""
SOCIAL_AUTH_FACEBOOK_SECRET = ""
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "696570367703-r6hc7mdd27t1sktdkivpnc5b25i0uip2.apps.googleusercontent.com"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "mApWNh3stCsYHwsGuWdbZWP8" # noqa

# To remove a useless warning in Django 1.7.
# See http://daniel.hepper.net/blog/2014/04/fixing-1_6-w001-when-upgrading-from-django-1-5-to-1-7/
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Properly handle HTTPS vs HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# /!\ WARNING : It will probably open security holes in your site if the proxy behing isn't well configured
# Read the docs for further informations - https://docs.djangoproject.com/en/1.7/ref/settings/#secure-proxy-ssl-header

# This tests whether the second commandline argument (after manage.py) was test
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
# Thread, SQLite and Django 1.7 doesn't work well together. For more info, you can checkout this ticket.
# https://code.djangoproject.com/ticket/12118. In Django 1.8, the problem have been solved.
# We need to create Thread in zds/search/utils.py, to improve perf at publication time.
# When we will use django 1.8, we can delete this param and change zds/search/utils.py.

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *
except ImportError:
    pass

