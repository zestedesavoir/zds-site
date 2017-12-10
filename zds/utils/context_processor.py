from copy import deepcopy

from django.conf import settings
from django.core.cache import cache

from git import Repo


def get_git_version():
    """
    Get Git version information.

    Since retrieving the Git version can be rather slow (due to I/O on
    the filesystem and, most importantly, forced garbage collections
    triggered by GitPython), you must consider using
    ``get_cached_git_version()`` (which behaves similarly).
    """
    try:
        repo = Repo(settings.BASE_DIR)
        branch = repo.active_branch
        commit = repo.head.commit.hexsha
        name = '{0}/{1}'.format(branch, commit[:7])
        return {'name': name, 'url': '{}/tree/{}'.format(settings.ZDS_APP['site']['repository']['url'], commit)}
    except (KeyError, TypeError):
        return {'name': '', 'url': ''}


def get_cached_git_version():
    """
    Get Git version information.

    Same as ``get_git_version()``, but cached with a simple timeout of
    one hour.
    """
    version = cache.get('git_version')
    if version is None:
        version = get_git_version()
        cache.set('git_version', version, 60 * 60)
    return version


def git_version(request):
    """
    A context processor to include the git version on all pages.
    """
    return {'git_version': get_cached_git_version()}


def app_settings(request):
    """
    A context processor with all APP settings.
    """
    app = deepcopy(settings.ZDS_APP)

    app['google_analytics_enabled'] = 'googleAnalyticsID' in app['site'] and \
                                      'googleTagManagerID' in app['site']

    return {
        'app': app,
    }
