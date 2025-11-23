from django.urls import path

from zds.tutorialv2.feeds import LastOpinionsFeedATOM, LastOpinionsFeedRSS
from zds.tutorialv2.views.display import ContainerOnlineView, OpinionOnlineView
from zds.tutorialv2.views.download_online import DownloadOnlineOpinion
from zds.tutorialv2.views.lists import ContentOfAuthor, ListOpinions

feed_patterns = [
    path("flux/rss/", LastOpinionsFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastOpinionsFeedATOM(), name="feed-atom"),
]

display_patterns = [
    path("<int:pk>/<slug:slug>/", OpinionOnlineView.as_view(), name="view"),
    path(
        "<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        ContainerOnlineView.as_view(),
        name="view-container",
    ),
    path("<int:pk>/<slug:slug>/<slug:container_slug>/", ContainerOnlineView.as_view(), name="view-container"),
]

download_patterns = [
    path("md/<int:pk>/<slug:slug>.md", DownloadOnlineOpinion.as_view(requested_file="md"), name="download-md"),
    path("pdf/<int:pk>/<slug:slug>.pdf", DownloadOnlineOpinion.as_view(requested_file="pdf"), name="download-pdf"),
    path("epub/<int:pk>/<slug:slug>.epub", DownloadOnlineOpinion.as_view(requested_file="epub"), name="download-epub"),
    path("zip/<int:pk>/<slug:slug>.zip", DownloadOnlineOpinion.as_view(requested_file="zip"), name="download-zip"),
    path("tex/<int:pk>/<slug:slug>.tex", DownloadOnlineOpinion.as_view(requested_file="tex"), name="download-tex"),
]

listing_patterns = [
    path("", ListOpinions.as_view(), name="list"),
    path(
        "voir/<str:username>/",
        ContentOfAuthor.as_view(type="OPINION", context_object_name="opinions"),
        name="find-opinion",
    ),
]

urlpatterns = feed_patterns + display_patterns + download_patterns + listing_patterns
