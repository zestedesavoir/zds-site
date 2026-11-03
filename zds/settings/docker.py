from .abstract_base import *

DEBUG = True

USE_L10N = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "zds_docker",
        "USER": "root",
        "PASSWORD": "zds_password",
        "HOST": "database",
        "PORT": "3306",
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "cache:11211",
    }
}

INSTALLED_APPS += (
    "debug_toolbar",
    "django_extensions",
)

ZDS_APP["zmd"]["server"] = "http://zmd:27272"
ZDS_APP["visual_changes"] = ["snow"]

ES_CONNECTIONS["default"]["hosts"] = ["elasticsearch:9200"]

ZDS_APP["very_top_banner"] = {
    "background_color": "#666",
    "border_color": "#353535",
    "color": "white",
    "message": "Version locale (docker)",
    "slug": "version-locale",
}
