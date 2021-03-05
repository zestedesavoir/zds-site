import requests

from django.conf import settings


class EnableMatomoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def matomo_track(self, request):
        matomo_api_url = "{0}/matomo.php".format(settings.ZDS_APP["site"]["matomoUrl"])
        matomo_site_id = settings.ZDS_APP["site"]["matomoID"]
        matomo_api_version = 1

        client_user_agent = request.META.get("HTTP_USER_AGENT", "")
        client_referer = request.META.get("HTTP_REFERER", "")
        client_accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        client_url = "{0}://{1}{2}".format(request.scheme, request.get_host(), request.path)

        requests.get(
            matomo_api_url,
            params={
                "idsite": matomo_site_id,
                "action_name": request.path,
                "rec": 1,
                "apiv": matomo_api_version,
                "lang": client_accept_language,
                "ua": client_user_agent,
                "urlref": client_referer,
                "url": client_url,
            },
        )

    def process_response(self, request, response):
        exclude_paths = ["/contenus", "/mp"]
        # only on get
        if request.method == "GET":
            for p in exclude_paths:
                if request.path.startswith(p):
                    return response
            self.matomo_track(request)

        return response
