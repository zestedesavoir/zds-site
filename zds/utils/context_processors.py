# encoding: utf-8

import django
import sys
from git import *
from django.conf import settings


def versions(request):
    return {
        'django_version': '{0}.{1}.{2}'.format(
            django.VERSION[0], django.VERSION[1], django.VERSION[2]),
        'python_version': '{0}.{1}.{2}'.format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2])
    }

def git_version(request):
    """Return the current git version.

    """
    repo = Repo(settings.SITE_ROOT)
    v = repo.head.commit.hexsha
    br = repo.active_branch

    return {
        'git_version': br+'-'+v[:5]
    }
