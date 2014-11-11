# coding: utf-8

from django.conf import settings


class Settings(object):
    def _setting(self, name, default_value):
        getter = lambda name, default_value: getattr(settings, name, default_value)
        return getter(name, default_value)

    @property
    def ADAPTER(self):
        return self._setting('ADAPTER', 'zds.member.adapters.DefaultMemberAdapter')

    @property
    def LOGIN_REDIRECT_URL(self):
        return self._setting('LOGIN_REDIRECT_URL', 'zds.pages.views.home')

    @property
    def FORMS(self):
        return self._setting('FORMS', {})


app_settings = Settings()
