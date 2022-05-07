from django.urls import path
from django.views.generic.base import RedirectView
from zds.tutorialv2.views.contributors import ContentOfContributors

from zds.tutorialv2.views.lists import TagsListView, ContentOfAuthor
from zds.tutorialv2.views.download_online import DownloadOnlineTutorial
from zds.tutorialv2.views.display import DisplayOnlineTutorial, DisplayOnlineContainer
from zds.tutorialv2.views.redirect import RedirectContentSEO, RedirectOldBetaTuto
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM


urlpatterns = [
    # flux
    path("flux/rss/", LastTutorialsFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastTutorialsFeedATOM(), name="feed-atom"),
    # view
    path(
        "<int:pk>/<slug:slug>/<int:p2>/<slug:parent_container_slug>/<int:p3>/<slug:container_slug>/",
        RedirectContentSEO.as_view(),
        name="redirect_old_tuto",
    ),
    path(
        "<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        DisplayOnlineContainer.as_view(),
        name="view-container",
    ),
    path("<int:pk>/<slug:slug>/<slug:container_slug>/", DisplayOnlineContainer.as_view(), name="view-container"),
    path("<int:pk>/<slug:slug>/", DisplayOnlineTutorial.as_view(), name="view"),
    # downloads:
    path("md/<int:pk>/<slug:slug>.md", DownloadOnlineTutorial.as_view(requested_file="md"), name="download-md"),
    path("html/<int:pk>/<slug:slug>.html", DownloadOnlineTutorial.as_view(requested_file="html"), name="download-html"),
    path("pdf/<int:pk>/<slug:slug>.pdf", DownloadOnlineTutorial.as_view(requested_file="pdf"), name="download-pdf"),
    path("epub/<int:pk>/<slug:slug>.epub", DownloadOnlineTutorial.as_view(requested_file="epub"), name="download-epub"),
    path("zip/<int:pk>/<slug:slug>.zip", DownloadOnlineTutorial.as_view(requested_file="zip"), name="download-zip"),
    path("tex/<int:pk>/<slug:slug>.tex", DownloadOnlineTutorial.as_view(requested_file="tex"), name="download-tex"),
    #  Old beta url compatibility
    path("beta/<int:pk>/<slug:slug>/", RedirectOldBetaTuto.as_view(), name="old-beta-url"),
    # Listing
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
