from django.conf import settings

from git import Repo


def get_git_version():
    """
    Get the git version of the site.
    """
    try:
        repo = Repo(settings.BASE_DIR)
        branch = repo.active_branch
        commit = repo.head.commit.hexsha
        name = '{0}/{1}'.format(branch, commit[:7])
        return {'name': name, 'url': '{}/tree/{}'.format(settings.ZDS_APP['site']['repository'], commit)}
    except (KeyError, TypeError):
        return {'name': '', 'url': ''}


def git_version(request):
    """
    A context processor to include the git version on all pages.
    """
    return {'git_version': get_git_version()}


def app_settings(request):
    """
    A context processor with all APP settings.
    """
    return {'app': settings.ZDS_APP}
