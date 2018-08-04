from copy import deepcopy

from django.conf import settings
from git import Repo, exc

from .header_notifications import get_header_notifications


def get_version():
    """
    Retrieve version informations from `zds/_version.py`.
    """
    try:
        repo = Repo(settings.BASE_DIR)
        branch = repo.active_branch
        commit = repo.head.commit.hexsha
        name = '{0}/{1}'.format(branch, commit[:7])
        return {'name': name, 'url': '{}/tree/{}'.format(settings.ZDS_APP['site']['repository']['url'], commit)}
    except (KeyError, TypeError, exc.InvalidGitRepositoryError):
        return {'name': '', 'url': ''}


def version(request):
    """
    A context processor to include the app version on all pages.
    """
    return {'zds_version': get_version()}


def header_notifications(request):
    user = request.user
    results = get_header_notifications(user)
    if results is None:
        # Unauthorized
        return {}
    # Prefix every key with `header_`
    return {'header_' + k: v for k, v in results.items()}


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
