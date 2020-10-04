from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = "zds.notification"

    def ready(self):
        from . import receivers  # noqa
