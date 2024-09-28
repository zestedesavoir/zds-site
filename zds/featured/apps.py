from django.apps import AppConfig


class FeaturedConfig(AppConfig):
    name = "zds.featured"

    def ready(self):
        from . import receivers  # noqa
