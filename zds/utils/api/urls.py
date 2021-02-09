from django.urls import path

from zds.utils.api.views import TagListAPI, UpdateCommentPotentialSpam

urlpatterns = [
    path("tags/", TagListAPI.as_view(), name="tags-list"),
    path(
        "messages/potential-spam/<int:pk>/", UpdateCommentPotentialSpam.as_view(), name="update-comment-potential-spam"
    ),
]
