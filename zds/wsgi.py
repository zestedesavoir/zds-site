# coding: utf-8

import os
from django.core.wsgi import get_wsgi_application

from zds.search2 import setup_es_connections

"""
WSGI config for zds project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zds.settings")

application = get_wsgi_application()

# setup ES
setup_es_connections()
