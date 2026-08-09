from django.apps import AppConfig


class AntispamConfig(AppConfig):
    name = "zds.antispam"

    def ready(self):
        from . import receivers  # noqa
