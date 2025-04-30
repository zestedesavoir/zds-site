import datetime

from django.conf import settings
from django.contrib.auth import logout

from zds.member.views import get_client_ip


class SetLastVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def process_response(self, request, response):
        # Update last visit time after request finished processing.
        user = None
        try:
            if request.user.is_authenticated:
                user = request.user
        except:
            pass

        if user:
            profile = request.user.profile
            if profile.last_visit is None:
                profile.last_visit = datetime.datetime.now()
                profile.last_ip_address = get_client_ip(request)
                profile.save()
            else:
                duration = datetime.datetime.now() - profile.last_visit
                if duration.seconds > settings.ZDS_APP["member"]["update_last_visit_interval"]:
                    profile.last_visit = datetime.datetime.now()
                    profile.last_ip_address = get_client_ip(request)
                    profile.save()
            if profile.is_banned():
                logout(request)
        return response
