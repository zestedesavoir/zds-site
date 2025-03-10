from django.urls import path

from zds.tutorialv2.api.views import (
    ContainerPublicationReadinessView,
    ContentReactionKarmaView,
    ExportsView,
    ExportView,
)

urlpatterns = [
    path(
        "reactions/<int:pk>/karma/",
        ContentReactionKarmaView.as_view(),
        name="reaction-karma",
    ),
    path(
        "publication/preparation/<int:pk>/",
        ContainerPublicationReadinessView.as_view(),
        name="readiness",
    ),
    path("export/<int:pk>/", ExportView.as_view(), name="generate_export"),
    path("exports/<int:pk>/", ExportsView.as_view(), name="list_exports"),
]
