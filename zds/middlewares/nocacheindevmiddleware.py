from django.conf import settings


class NoCacheInDevMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def process_response(self, request, response):
        """
        Set the "Cache-Control" header to "must-revalidate, no-cache" for JS
        and CSS files.
        """
        if request.path.startswith(settings.STATIC_URL) and (
            request.path.endswith(".js") or request.path.endswith(".css")
        ):
            response["Cache-Control"] = "must-revalidate, no-cache"
            response["Last-Modified"] = ""
        return response
