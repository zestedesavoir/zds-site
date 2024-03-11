from datetime import datetime

from zds.member.views import get_client_ip


class ManageSessionsMiddleware:
    """This middleware adds the current IP address, user agent and timestamp to user sessions.
    This gives them the information they need to manage their sessions, and possibly delete some of them."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def process_response(self, request, response):
        try:
            user = request.user
        except AttributeError:
            user = None

        if user is not None and user.is_authenticated:
            session = request.session
            session["ip_address"] = get_client_ip(request)
            session["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
            session["last_visit"] = datetime.now().timestamp()
        return response
