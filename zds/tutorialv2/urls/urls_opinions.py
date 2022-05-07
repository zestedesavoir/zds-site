from django.urls import path, path

from zds.tutorialv2.feeds import LastOpinionsFeedRSS, LastOpinionsFeedATOM
from zds.tutorialv2.views.lists import ListOpinions, ContentOfAuthor
from zds.tutorialv2.views.download_online import DownloadOnlineOpinion
from zds.tutorialv2.views.display import DisplayOnlineOpinion

urlpatterns = [
    # Flux
    path("flux/rss/", LastOpinionsFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastOpinionsFeedATOM(), name="feed-atom"),
    # View
    path("<int:pk>/<slug:slug>/", DisplayOnlineOpinion.as_view(), name="view"),
    # downloads:
    path("md/<int:pk>/<slug:slug>.md", DownloadOnlineOpinion.as_view(requested_file="md"), name="download-md"),
    path(
        "html/<int:pk>/<slug:slug>.html",
        DownloadOnlineOpinion.as_view(requested_file="html"),
        name="download-html",
    ),
    path("pdf/<int:pk>/<slug:slug>.pdf", DownloadOnlineOpinion.as_view(requested_file="pdf"), name="download-pdf"),
    path(
        "epub/<int:pk>/<slug:slug>.epub",
        DownloadOnlineOpinion.as_view(requested_file="epub"),
        name="download-epub",
    ),
    path("zip/<int:pk>/<slug:slug>.zip", DownloadOnlineOpinion.as_view(requested_file="zip"), name="download-zip"),
    path("tex/<int:pk>/<slug:slug>.tex", DownloadOnlineOpinion.as_view(requested_file="tex"), name="download-tex"),
    # Listing
    path("", ListOpinions.as_view(), name="list"),
    path(
        "voir/<str:username>/",
        ContentOfAuthor.as_view(type="OPINION", context_object_name="opinions", sort="creation"),
        name="find-opinion",
    ),
]
