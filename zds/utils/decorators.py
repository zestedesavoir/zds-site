from django.conf import settings
from django.http import HttpResponseRedirect


def https_required(func):
    """
    Check if the decorator is enabled, the request is unsecured and redirect the visitor in HTTPS.
    """
    def _https_required(request, *args, **kwargs):
        if getattr(settings, 'ENABLE_HTTPS_DECORATOR', False) and not request.is_secure():
            # Code from http://www.redrobotstudios.com/blog/2009/02/18/securing-django-with-ssl/
            request_url = request.build_absolute_uri(request.get_full_path())
            secure_url = request_url.replace('http://', 'https://')
            return HttpResponseRedirect(secure_url)

        return func(request, *args, **kwargs)
    return _https_required
