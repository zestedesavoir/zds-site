# coding: utf-8

import os
import sys
from os.path import join

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

INTERNAL_IPS = ('127.0.0.1',)  # debug toolbar

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'base.db'),
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
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://media.lawrence.com/media/', 'http://example.com/media/'
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' 'static/' subdirectories and in STATICFILES_DIRS.
# Example: '/home/media/media.lawrence.com/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: 'http://media.lawrence.com/static/'
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n!01nl+318#x75_%le8#s0=-*ysw&amp;y49uc#t=*wvi(9hnyii0z'  # noqa

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
    'zds.middlewares.profile.ProfileMiddleware',
)

ROOT_URLCONF = 'zds.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'zds.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
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
                'zds.utils.context_processor.git_version',
            ],
            'debug': DEBUG,
        }
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
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
        'featured': {'size': (228, 228), 'crop': True},
        'gallery_illu': {'size': (480, 270), 'crop': True},
        'content': {'size': (960, 960), 'crop': False},
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'zds.api.pagination.DefaultPagination',
    # Active OAuth2 authentication.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
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
    'exclude_namespaces': [
        'content',
        'forum'
    ],
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
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'DEBUG',
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

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

LOGIN_URL = '/membres/connexion'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: '/membres/voir/{0}/'.format(urlquote(u.username.encode('utf-8')))
}


# Django fileserve settings (set to True for local dev version only)
SERVE = False

PANDOC_LOC = ''
PANDOC_PDF_PARAM = ('--latex-engine=xelatex '
                    '--template={} -s -S -N '
                    '--toc -V documentclass=scrbook -V lang=francais '
                    '-V mainfont=Merriweather -V monofont="SourceCodePro-Regular" '
                    '-V fontsize=12pt -V geometry:margin=1in '.format(join('..', '..', '..',
                                                                           'assets', 'tex', 'template.tex')))
# LOG PATH FOR PANDOC LOGGING
PANDOC_LOG = './pandoc.log'
PANDOC_LOG_STATE = False

ES_ENABLED = True

ES_CONNECTIONS = {
    'default': {
        'hosts': ['localhost:9200'],
    }
}

ES_SEARCH_INDEX = {
    'name': 'zds_search',
    'shards': 3,
    'replicas': 0,
}

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

# best quality, 100 is the same but documentation says
# ' values up to 100 are allowed, but this is not recommended'
# so let's use 95
THUMBNAIL_QUALITY = 95
# Let's use the default value BUT if we want to let png in lossless format, we have tu use (png,) instead of None
THUMBNAIL_PRESERVE_EXTENSIONS = None


ZDS_APP = {
    'site': {
        'name': u'ZesteDeSavoir',
        'litteral_name': u'Zeste de Savoir',
        'slogan': u'Zeste de Savoir, la connaissance pour tous et sans pépins',
        'abbr': u'zds',
        'url': u'http://127.0.0.1:8000',
        'secure_url': u'https://127.0.0.1:8000',
        'dns': u'zestedesavoir.com',
        'email_contact': u'zestedesavoir@gmail.com',
        'email_noreply': u'noreply@zestedesavoir.com',
        'forum_feedback_users': u'/forums/communaute/bug-suggestions/',
        'contribute_link': u'https://github.com/zestedesavoir/zds-site/blob/dev/CONTRIBUTING.md',
        'short_description': u'',
        'long_description': u'Zeste de Savoir est un site de partage de connaissances '
                            u'sur lequel vous trouverez des tutoriels de tous niveaux, '
                            u'des articles et des forums d’entraide animés par et pour '
                            u'la communauté.',
        'association': {
            'name': u'Zeste de Savoir',
            'fee': u'20 €',
            'email': u'zestedesavoir@gmail.com',
            'email_ca': u'ca-zeste-de-savoir@googlegroups.com',
            'forum_ca_pk': 25
        },
        'repository': {
            'url': u'https://github.com/zestedesavoir/zds-site',
            'bugtracker': u'https://github.com/zestedesavoir/zds-site/issues',
            'api': u'https://api.github.com/repos/zestedesavoir/zds-site',
            'tags': [
                u'C-Back', u'C-Front', u'C-API', u'C-Documentation', u'C-Infra', u'S-Bug', u'S-Régression',
                u'S-Évolution'
            ]
        },
        'licenses': {
            'logo': {
                'code': u'CC-BY',
                'title': u'Creative Commons License',
                'description': u'Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - '
                               u'Partage dans les Mêmes Conditions 4.0 International.',
                'url_image': u'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': u'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'author': u'MaxRoyo'
            },
            'cookies': {
                'code': u'CC-BY',
                'title': u'Licence Creative Commons',
                'description': u'licence Creative Commons Attribution 4.0 International',
                'url_image': u'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': u'http://creativecommons.org/licenses/by-nc-sa/4.0/'
            },
            'source': {
                'code': u'GPL v3',
                'url_license': u'http://www.gnu.org/licenses/gpl-3.0.html',
                'provider_name': u'Progdupeupl',
                'provider_url': u'http://pdp.microjoe.org',
            },
            'licence_info_title': u'http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-lic'
                                  u'ences-sur-zeste-de-savoir/',
            'licence_info_link': u'Le droit d\'auteur, Creative Commons et les licences sur Zeste de Savoir'
        },
        'hosting': {
            'name': u'GANDI SAS',
            'address': u'63-65 boulevard Massena - 75013 Paris - France'
        },
        'social': {
            'facebook': u'https://www.facebook.com/ZesteDeSavoir',
            'twitter': u'https://twitter.com/ZesteDeSavoir',
            'googleplus': u'https://plus.google.com/u/0/107033688356682807298'
        },
        'cnil': u'1771020',
    },
    'member': {
        'bot_account': u'admin',
        'anonymous_account': u'anonymous',
        'external_account': u'external',
        'bot_group': u'bot',
        'dev_group': u'devs',
        'members_per_page': 100,
        'update_last_visit_interval': 600,  # seconds
    },
    'gallery': {
        'image_max_size': 1024 * 1024,
        'gallery_per_page': 21,
        'images_per_page': 21,
    },
    'article': {
        'home_number': 3,
        'repo_path': os.path.join(BASE_DIR, 'articles-data')
    },
    'opinions': {
        'home_number': 5,
        'repo_path': os.path.join(BASE_DIR, 'opinions-data')
    },
    'tutorial': {
        'repo_path': os.path.join(BASE_DIR, 'tutoriels-private'),
        'repo_public_path': os.path.join(BASE_DIR, 'tutoriels-public'),
        'default_licence_pk': 7,
        'home_number': 4,
        'helps_per_page': 20,
        'content_per_page': 42,
        'feed_length': 5,
    },
    'content': {
        'repo_private_path': os.path.join(BASE_DIR, 'contents-private'),
        'repo_public_path': os.path.join(BASE_DIR, 'contents-public'),
        'extra_contents_dirname': 'extra_contents',
        # can also be 'extra_content_generation_policy': 'WATCHDOG'
        # or 'extra_content_generation_policy': 'NOTHING'
        'extra_content_generation_policy': 'SYNC',
        'extra_content_watchdog_dir': os.path.join(BASE_DIR, 'watchdog-build'),
        'max_tree_depth': 3,
        'default_licence_pk': 7,
        'content_per_page': 60,
        'notes_per_page': 25,
        'helps_per_page': 20,
        'commits_per_page': 20,
        'feed_length': 5,
        'user_page_number': 5,
        'default_image': os.path.join(BASE_DIR, 'fixtures', 'noir_black.png'),
        'import_image_prefix': 'archive',
        'build_pdf_when_published': True,
        'maximum_slug_size': 150,
        'sec_per_minute': 1500
    },
    'forum': {
        'posts_per_page': 21,
        'topics_per_page': 21,
        'spam_limit_seconds': 60 * 15,
        'spam_limit_participant': 2,
        'beta_forum_id': 1,
        'max_post_length': 1000000,
        'top_tag_max': 5,
        'home_number': 5,
        'old_post_limit_days': 90,
        # Exclude tags from top tags list. Tags listed here should not be relevant for most of users.
        # Be warned exclude too much tags can restrict performance
        'top_tag_exclu': ['bug', 'suggestion', 'tutoriel', 'beta', 'article']
    },
    'topic': {
        'home_number': 5,
    },
    'comment': {
        'max_pings': 15,
        'enable_pings': True,
    },
    'featured_resource': {
        'featured_per_page': 100,
        'home_number': 5,
    },
    'notification': {
        'per_page': 50,
    },
    'paginator': {
        'folding_limit': 4
    },
    'search': {
        'mark_keywords': ['javafx', 'haskell', 'groovy', 'powershell', 'latex', 'linux', 'windows'],
        'results_per_page': 20,
        'search_groups': {
            'content': (
                _(u'Contenus publiés'), ['publishedcontent', 'chapter']
            ),
            'topic': (
                _(u'Sujets du forum'), ['topic']
            ),
            'post': (
                _(u'Messages du forum'), ['post']
            ),
        },
        'boosts': {
            'publishedcontent': {
                'global': 3.0,
                'if_article': 1.0,
                'if_tutorial': 1.0,
            },
            'topic': {
                'global': 2.0,
                'if_solved': 1.1,
                'if_sticky': 1.2,
                'if_locked': 0.1,
            },
            'chapter': {
                'global': 1.5,
            },
            'post': {
                'global': 1.0,
                'if_first': 1.2,
                'if_useful': 1.5,
                'ld_ratio_above_1': 1.05,
                'ld_ratio_below_1': 0.95,
            }
        }
    },
    'visual_changes': [],
    'display_search_bar': True
}

LOGIN_REDIRECT_URL = '/'

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
SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '696570367703-r6hc7mdd27t1sktdkivpnc5b25i0uip2.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'mApWNh3stCsYHwsGuWdbZWP8'  # noqa

# ReCaptcha stuff
USE_CAPTCHA = False
NOCAPTCHA = True  # Use the 'No Captcha engine'
RECAPTCHA_USE_SSL = True
# keys (should be overriden in the settings_prod.py file)
RECAPTCHA_PUBLIC_KEY = 'dummy'  # noqa
RECAPTCHA_PRIVATE_KEY = 'dummy'  # noqa

# Anonymous [Dis]Likes. Authors of [dis]likes before those pk will never be shown
VOTES_ID_LIMIT = 0

# To remove a useless warning in Django 1.7.
# See http://daniel.hepper.net/blog/2014/04/fixing-1_6-w001-when-upgrading-from-django-1-5-to-1-7/
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'
}

# Properly handle HTTPS vs HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *  # noqa
except ImportError:
    pass

# MUST BE after settings_prod import
if DEBUG:
    INSTALLED_APPS += (
        'debug_toolbar',
    )
