from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import is_valid_path, reverse

from zds.member.forms import LoginForm
from zds.member.views import get_client_ip


class LoginView(LoginView):
    form_class = LoginForm
    template_name = "member/login.html"

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        # Display errors in error/info bars instead of the form built-in display.
        for error in form.errors.values():
            messages.error(self.request, error[0])
        form.form_show_errors = False
        return super().form_invalid(form)

    def form_valid(self, form):
        if "remember" not in self.request.POST:
            self.request.session.set_expiry(0)
        form.user_cache.profile.last_ip_address = get_client_ip(self.request)
        form.user_cache.profile.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["next"] = self.get_success_url()
        return kwargs

    def get_success_url(self):
        """In case of success, redirect to homepage for some special 'next' targets or non-existing pages."""
        url = self.get_redirect_url()
        if self.is_special(url) or not is_valid_path(url):
            url = settings.LOGIN_REDIRECT_URL
        return url

    @staticmethod
    def is_special(url):
        """Determine if `url` is a special case for redirection."""
        names = ["member-login", "register-member", "member-logout"]
        urls = [reverse(name) for name in names]
        return url in urls
