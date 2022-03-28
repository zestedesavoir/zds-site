from copy import deepcopy

from django.conf import settings

from zds import __version__, git_version

from .header_notifications import get_header_notifications


def get_version():
    """
    Retrieve version informations from `zds/_version.py`.
    """
    if git_version is not None:
        name = f"{__version__}/{git_version[:7]}"
        url = get_repository_url(settings.ZDS_APP["github_projects"]["default_repository"], "base_url")
        return {"name": name, "url": f"{url}/tree/{git_version}"}
    else:
        return {"name": __version__, "url": None}


def get_repository_url(repository_name, url_type):
    if repository_name not in settings.ZDS_APP["github_projects"]["repositories"]:
        raise Exception("Incorrect repository_name: " + repository_name)

    return settings.ZDS_APP["github_projects"][url_type](repository_name)


def version(request):
    """
    A context processor to include the app version on all pages.
    """
    return {"zds_version": get_version()}


def header_notifications(request):
    user = request.user
    results = get_header_notifications(user)
    if results is None:
        # Unauthorized
        return {}
    # Prefix every key with `header_`
    return {"header_" + k: v for k, v in results.items()}


def app_settings(request):
    """
    A context processor with all APP settings.
    """
    app = deepcopy(settings.ZDS_APP)

    return {
        "app": app,
    }
