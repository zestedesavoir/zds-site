from importlib import import_module

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from zds.member.utils import get_geo_location_from_ip, get_info_from_user_agent
from zds.utils.paginator import ZdSPagingListView

Session = import_module(settings.SESSION_ENGINE).CustomSession
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class ListSessions(LoginRequiredMixin, ZdSPagingListView):
    """List the user's sessions with useful information (user agent, IP address, geolocation and last visit)."""

    model = Session
    context_object_name = "sessions"
    template_name = "member/settings/sessions.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        self.object_list = []
        for session in Session.objects.filter(account_id=self.request.user.pk).iterator():
            data = session.get_decoded()
            session_context = {
                "session_key": session.session_key,
                "user_agent": get_info_from_user_agent(data.get("user_agent", "")),
                "ip_address": data.get("ip_address", ""),
                "geolocation": get_geo_location_from_ip(data.get("ip_address", "")) or _("Inconnue"),
                "last_visit": data.get("last_visit", 0),
                "is_active": session.session_key == self.request.session.session_key,
            }

            if session_context["is_active"]:
                self.object_list.insert(0, session_context)
            else:
                self.object_list.append(session_context)

        return super().get_context_data(**kwargs)


class DeleteSession(LoginRequiredMixin, View):
    """Delete a user's session."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        session_key = request.POST.get("session_key", None)
        if session_key and session_key != self.request.session.session_key:
            session = SessionStore(session_key=session_key)
            if session.get("_auth_user_id", "") == str(self.request.user.pk):
                session.flush()

        return redirect(reverse("list-sessions"))
