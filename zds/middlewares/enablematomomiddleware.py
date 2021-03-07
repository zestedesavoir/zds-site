from queue import Queue

import requests

from django.conf import settings
from threading import Thread

matomo_api_url = "{0}/matomo.php".format(settings.ZDS_APP["site"]["matomoUrl"])
matomo_site_id = settings.ZDS_APP["site"]["matomoID"]
matomo_api_version = 1


def _background_process(queue: Queue):
    data = queue.get(block=True)
    while data:
        print("toto")
        requests.get(
            matomo_api_url,
            params={
                "idsite": matomo_site_id,
                "action_name": data["r_path"],
                "rec": 1,
                "apiv": matomo_api_version,
                "lang": data["client_accept_language"],
                "ua": data["client_user_agent"],
                "urlref": data["client_referer"],
                "url": data["client_url"],
            },
        )
        data = queue.get(block=True)


class EnableMatomoMiddleware:
    def __init__(self, get_response):

        self.get_response = get_response
        self.queue = Queue()
        self.worker = Thread(target=_background_process, args=(self.queue,))
        print("will start")
        self.worker.start()
        print("started")

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def matomo_track(self, request):
        client_user_agent = request.META.get("HTTP_USER_AGENT", "")
        client_referer = request.META.get("HTTP_REFERER", "")
        client_accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        client_url = "{0}://{1}{2}".format(request.scheme, request.get_host(), request.path)
        r_path = request.path
        print("put")
        self.queue.put(
            {
                "client_user_agent": client_user_agent,
                "client_referer": client_referer,
                "client_accept_language": client_accept_language,
                "client_url": client_url,
                "r_path": r_path,
            }
        )
        print("is async?")

    def process_response(self, request, response):
        exclude_paths = ["/contenus", "/mp", "/munin"]
        # only on get
        if request.method == "GET":
            for p in exclude_paths:
                if request.path.startswith(p):
                    return response
            self.matomo_track(request)

        return response

    def __del__(self):
        self.queue.put(False)
        self.worker.join()
