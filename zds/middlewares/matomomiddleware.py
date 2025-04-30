import logging
from queue import Queue
from threading import Thread

import requests
from _datetime import datetime
from django.conf import settings
from django.urls import reverse

from zds.member.views import get_client_ip
from zds.utils.misc import is_ajax

matomo_token_auth = settings.ZDS_APP["site"]["matomo_token_auth"]
matomo_api_url = "{}/matomo.php?token_auth={}".format(settings.ZDS_APP["site"]["matomo_url"], matomo_token_auth)
matomo_site_id = settings.ZDS_APP["site"]["matomo_site_id"]
matomo_api_version = 1
logger = logging.getLogger(__name__)
tracked_status_code = [200]
tracked_methods = ["GET"]
excluded_paths = ["/contenus", "/mp", "/munin", "/api", "/static", "/media"]


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
        if "search" in data:
            params["search"] = data["search"]
            params["search_cat"] = data["search_cat"]
            params["search_count"] = data["search_count"]
        try:
            if data["address_ip"] != "0.0.0.0":
                params["cip"] = data["address_ip"]
            requests.get(
                matomo_api_url,
                params=params,
            )
            logger.info(f'Matomo tracked this link : {data["client_url"]}')
        except Exception:
            logger.exception(f'Something went wrong with the tracking of the link {data["client_url"]}')

        data = queue.get(block=True)


def _compute_search_category(request):
    categories = []
    models = request.GET.get("models", [])
    categories.append("-" if "content" not in models else "content")
    categories.append("-" if "post" not in models else "post")
    categories.append("-" if "topic" not in models else "topic")
    return "|".join(categories)


class MatomoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.queue = Queue()
        if settings.ZDS_APP["site"]["matomo_tracking_enabled"]:
            self.worker = Thread(target=_background_process, args=(self.queue,))
            self.worker.setDaemon(True)
            self.worker.start()

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def matomo_track(self, request, search_data=None):
        client_user_agent = request.META.get("HTTP_USER_AGENT", "")
        client_referer = request.META.get("HTTP_REFERER", "")
        client_accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        client_url = f"{request.scheme}://{request.get_host()}{request.path}"
        if settings.ZDS_APP["site"]["matomo_tracking_enabled"]:
            tracking_params = {
                "client_user_agent": client_user_agent,
                "client_referer": client_referer,
                "client_accept_language": client_accept_language,
                "client_url": client_url,
                "datetime": datetime.now().time(),
                "r_path": request.path,
                "address_ip": get_client_ip(request),
            }
            if search_data:
                tracking_params.update(search_data)
            self.queue.put(tracking_params)

    def process_response(self, request, response):
        if response.status_code not in tracked_status_code or is_ajax(request):
            return response
        # only on get
        if request.method in tracked_methods:
            for p in excluded_paths:
                if request.path.startswith(p):
                    return response
            try:
                if (
                    reverse("search:query") in request.path
                    and hasattr(response, "context_data")
                    and response.context_data["object_list"]
                ):
                    self.matomo_track(
                        request,
                        search_data={
                            "search": request.GET.get("q", "unknown"),
                            "search_cat": _compute_search_category(request),
                            # use paginator.count instead of object_list.count()
                            # django paginator uses a cached_property for count method and that's far more
                            # performant than querying es for counting purpose
                            "search_count": response.context_data["paginator"].count,
                        },
                    )
                else:
                    self.matomo_track(request)
            except Exception:
                logger.exception(f"Something failed with Matomo tracking system.")

        return response

    def __del__(self):
        if settings.ZDS_APP["site"]["matomo_tracking_enabled"]:
            self.queue.put(False)
            self.worker.join(timeout=2)
