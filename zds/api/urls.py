from django.urls import include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="",
        default_version="",
        description="",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name=""),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r"^$", schema_view.with_ui("swagger", cache_timeout=0), name="docs"),
    re_path(r"^contenus/", include(("zds.tutorialv2.api.urls", "zds.tutorialv2.api"), namespace="content")),
    re_path(r"^forums/", include(("zds.forum.api.urls", "zds.forum.api"), namespace="forum")),
    re_path(r"^galeries/", include(("zds.gallery.api.urls", "zds.gallery.api"), namespace="gallery")),
    re_path(r"^membres/", include(("zds.member.api.urls", "zds.member.api"), namespace="member")),
    re_path(r"^mps/", include(("zds.mp.api.urls", "zds.mp.api"), namespace="mp")),
    re_path(r"^", include(("zds.utils.api.urls", "zds.utils.api"), namespace="utils")),
    re_path(
        r"^notifications/", include(("zds.notification.api.urls", "zds.notification.api"), namespace="notification")
    ),
]
