from copy import deepcopy

from django.conf import settings

from zds import __version__, git_version

from .header_notifications import get_header_notifications


def get_version():
    """
    Retrieve version informations from `zds/_version.py`.
    """
    if git_version is not None:
        name = "{0}/{1}".format(__version__, git_version[:7])
        url = settings.ZDS_APP["site"]["repository"]["url"]
        return {"name": name, "url": "{}/tree/{}".format(url, git_version)}
    else:
        return {"name": __version__, "url": None}


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

    app["google_analytics_enabled"] = "googleAnalyticsID" in app["site"] and "googleTagManagerID" in app["site"]

    return {
        "app": app,
    }
