from _datetime import datetime
from queue import Queue

import requests
import logging

from django.conf import settings
from threading import Thread

matomo_api_url = "{}/matomo.php".format(settings.ZDS_APP["site"]["matomoUrl"])
matomo_site_id = settings.ZDS_APP["site"]["matomoSiteID"]
matomo_api_version = 1
logger = logging.getLogger(__name__)
tracked_status_code = [200]
tracked_methods = ["GET"]
excluded_paths = ["/contenus", "/mp", "/munin", "/api"]


def _background_process(queue: Queue):
    data = queue.get(block=True)
    while data:
        params = {
            "idsite": matomo_site_id,
            "action_name": data["r_path"],
            "rec": 1,
            "apiv": matomo_api_version,
            "lang": data["client_accept_language"],
            "ua": data["client_user_agent"],
            "urlref": data["client_referer"],
            "url": data["client_url"],
            "h": data["datetime"].hour,
            "m": data["datetime"].minute,
            "s": data["datetime"].second,
        }
        try:
            requests.get(
                matomo_api_url,
                params=params,
            )
            logger.info(f'Matomo tracked this link : {data["client_url"]}')
        except Exception:
            logger.error(f'Something went wrong with the tracking of the link {data["client_url"]}')

        data = queue.get(block=True)


class MatomoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.queue = Queue()
        if settings.ZDS_APP["site"].get("matomo_enabled", True):
            self.worker = Thread(target=_background_process, args=(self.queue,))
            self.worker.setDaemon(True)
            self.worker.start()

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def matomo_track(self, request):
        client_user_agent = request.META.get("HTTP_USER_AGENT", "")
        client_referer = request.META.get("HTTP_REFERER", "")
        client_accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        client_url = f"{request.scheme}://{request.get_host()}{request.path}"
        if settings.ZDS_APP["site"].get("matomo_enabled", True):
            self.queue.put(
                {
                    "client_user_agent": client_user_agent,
                    "client_referer": client_referer,
                    "client_accept_language": client_accept_language,
                    "client_url": client_url,
                    "datetime": datetime.now().time(),
                    "r_path": request.path,
                }
            )

    def process_response(self, request, response):
        if response.status_code not in tracked_status_code:
            return response
        # only on get
        if request.method in tracked_methods:
            for p in excluded_paths:
                if request.path.startswith(p):
                    return response
            try:
                self.matomo_track(request)
            except Exception as e:
                logger.error(f"Something failed : {str(e)}")

        return response

    def __del__(self):
        if settings.ZDS_APP["site"].get("matomo_enabled", True):
            self.queue.put(False)
            self.worker.join(timeout=2)
