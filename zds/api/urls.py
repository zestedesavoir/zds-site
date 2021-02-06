from django.urls import re_path, include

from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view()

urlpatterns = [
    re_path(r"^$", schema_view, name="docs"),
    re_path(r"^contenus/", include(("zds.tutorialv2.api.urls", "zds.tutorialv2.api"), namespace="content")),
    re_path(r"^forums/", include(("zds.forum.api.urls", "zds.forum.api"), namespace="forum")),
    re_path(r"^galeries/", include(("zds.gallery.api.urls", "zds.gallery.api"), namespace="gallery")),
    re_path(r"^membres/", include(("zds.member.api.urls", "zds.member.api"), namespace="member")),
    re_path(r"^mps/", include(("zds.mp.api.urls", "zds.mp.api"), namespace="mp")),
    re_path(r"^tags/", include(("zds.utils.api.urls", "zds.utils.api"), namespace="tag")),
    re_path(
        r"^notifications/", include(("zds.notification.api.urls", "zds.notification.api"), namespace="notification")
    ),
]
