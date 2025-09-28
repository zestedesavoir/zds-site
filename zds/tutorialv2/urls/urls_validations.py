from django.urls import path

from zds.tutorialv2.views.validations_contents import (
    AcceptValidation,
    AskValidationForContent,
    CancelValidation,
    MarkObsolete,
    RejectValidation,
    ReserveValidation,
    RevokeValidation,
    ValidationHistoryView,
    ValidationListView,
)
from zds.tutorialv2.views.validations_opinions import (
    DoNotPickOpinion,
    PickOpinion,
    PromoteOpinionToArticle,
    PublishOpinion,
    RevokePickOperation,
    UnpickOpinion,
    UnpublishOpinion,
    ValidationOpinionListView,
)

urlpatterns = [
    path("historique/<int:pk>/<slug:slug>/", ValidationHistoryView.as_view(), name="history"),
    # VALIDATION BEFORE PUBLICATION
    path("proposer/<int:pk>/<slug:slug>/", AskValidationForContent.as_view(), name="ask"),
    path("reserver/<int:pk>/", ReserveValidation.as_view(), name="reserve"),
    path("annuler/<int:pk>/", CancelValidation.as_view(), name="cancel"),
    path("refuser/<int:pk>/", RejectValidation.as_view(), name="reject"),
    path("accepter/<int:pk>/", AcceptValidation.as_view(), name="accept"),
    path("revoquer/<int:pk>/<slug:slug>/", RevokeValidation.as_view(), name="revoke"),
    # NO VALIDATION BEFORE PUBLICATION
    path("publier/<int:pk>/<slug:slug>/", PublishOpinion.as_view(), name="publish-opinion"),
    path("depublier/<int:pk>/<slug:slug>/", UnpublishOpinion.as_view(), name="unpublish-opinion"),
    path("choisir/<int:pk>/<slug:slug>/", PickOpinion.as_view(), name="pick-opinion"),
    path("ignorer/<int:pk>/<slug:slug>/", DoNotPickOpinion.as_view(), name="ignore-opinion"),
    path("operation/annuler/<int:pk>/", RevokePickOperation.as_view(), name="revoke-ignore-opinion"),
    path("retirer/<int:pk>/<slug:slug>/", UnpickOpinion.as_view(), name="unpick-opinion"),
    path("promouvoir/<int:pk>/<slug:slug>/", PromoteOpinionToArticle.as_view(), name="promote-opinion"),
    path("marquer-obsolete/<int:pk>/", MarkObsolete.as_view(), name="mark-obsolete"),
    # VALIDATION VIEWS FOR STAFF
    path("billets/", ValidationOpinionListView.as_view(), name="list-opinion"),
    path("", ValidationListView.as_view(), name="list"),
]
