from django.urls import path
from django.views.generic.base import RedirectView

from zds.tutorialv2.feeds import LastTutorialsFeedATOM, LastTutorialsFeedRSS
from zds.tutorialv2.views.contributors import ContentOfContributors
from zds.tutorialv2.views.display import ContainerOnlineView, TutorialOnlineView
from zds.tutorialv2.views.download_online import DownloadOnlineTutorial
from zds.tutorialv2.views.lists import ContentOfAuthor, TagsListView
from zds.tutorialv2.views.redirect import RedirectContentSEO, RedirectOldBetaTuto

feed_patterns = [
    path("flux/rss/", LastTutorialsFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastTutorialsFeedATOM(), name="feed-atom"),
]

display_patterns = [
    path(
        "<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        ContainerOnlineView.as_view(),
        name="view-container",
    ),
    path("<int:pk>/<slug:slug>/<slug:container_slug>/", ContainerOnlineView.as_view(), name="view-container"),
    path("<int:pk>/<slug:slug>/", TutorialOnlineView.as_view(), name="view"),
]

download_patterns = [
    path("md/<int:pk>/<slug:slug>.md", DownloadOnlineTutorial.as_view(requested_file="md"), name="download-md"),
    path("pdf/<int:pk>/<slug:slug>.pdf", DownloadOnlineTutorial.as_view(requested_file="pdf"), name="download-pdf"),
    path("epub/<int:pk>/<slug:slug>.epub", DownloadOnlineTutorial.as_view(requested_file="epub"), name="download-epub"),
    path("zip/<int:pk>/<slug:slug>.zip", DownloadOnlineTutorial.as_view(requested_file="zip"), name="download-zip"),
    path("tex/<int:pk>/<slug:slug>.tex", DownloadOnlineTutorial.as_view(requested_file="tex"), name="download-tex"),
]

listing_patterns = [
    path("", RedirectView.as_view(pattern_name="publication:list", permanent=True)),
    path("tags/", TagsListView.as_view(displayed_types=["TUTORIAL"]), name="tags"),
    path(
        "voir/<str:username>/",
        ContentOfAuthor.as_view(type="TUTORIAL", context_object_name="tutorials"),
        name="find-tutorial",
    ),
    path(
        "contributions/<str:username>/",
        ContentOfContributors.as_view(type="TUTORIAL", context_object_name="contribution_tutorials"),
        name="find-contributions-tutorial",
    ),
]

redirect_patterns = [
    path(
        "<int:pk>/<slug:slug>/<int:p2>/<slug:parent_container_slug>/<int:p3>/<slug:container_slug>/",
        RedirectContentSEO.as_view(),
        name="redirect_old_tuto",
    ),
    path("beta/<int:pk>/<slug:slug>/", RedirectOldBetaTuto.as_view(), name="old-beta-url"),
]

urlpatterns = feed_patterns + display_patterns + download_patterns + listing_patterns + redirect_patterns
