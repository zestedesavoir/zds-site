from django.conf import settings
from django.http import HttpResponseRedirect


class ForceHttpsMembersMiddleware(object):
    """
    Check if the middleware is enabled, the request is unsecured, the user is authenticated and redirect the user
    in HTTPS.
    """

    def process_request(self, request):
        if getattr(settings, 'FORCE_HTTPS_FOR_MEMBERS', False) and not request.is_secure():
            if request.user.is_authenticated():
                # Code from http://www.redrobotstudios.com/blog/2009/02/18/securing-django-with-ssl/
                request_url = request.build_absolute_uri(request.get_full_path())
                secure_url = request_url.replace('http://', 'https://')
                return HttpResponseRedirect(secure_url)
