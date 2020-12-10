from colorlog import ColoredFormatter

from .abstract_base import *
from .abstract_test import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "ci_db_name",
        "USER": "root",
        "PASSWORD": "ci_root_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

for logger in LOGGING["loggers"].values():
    logger["level"] = "ERROR"
    logger["formatters"] = {
        "verbose": {
            "()": ColoredFormatter,
            "format": "%(log_color)s %(levelname)s %(reset)s %(bold_black)s%(name)s%(reset)s %(message)s",
            "log_colors": {
                "DEBUG": "fg_white,bg_black",
                "INFO": "fg_black,bg_bold_white",
                "WARNING": "fg_black,bg_bold_yellow",
                "ERROR": "fg_bold_white,bg_bold_red",
                "CRITICAL": "fg_bold_white,bg_bold_red",
            },
        },
        "django.server": {
            "()": ColoredFormatter,
            "format": "%(log_color)s%(message)s",
            "log_colors": {
                "INFO": "bold_black",
                "WARNING": "bold_yellow",
                "ERROR": "bold_red",
                "CRITICAL": "bold_red",
            },
        },
    }
