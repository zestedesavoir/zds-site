from django.urls import path, re_path

from zds.tutorialv2.feeds import LastOpinionsFeedRSS, LastOpinionsFeedATOM
from zds.tutorialv2.views.lists import ListOpinions, ContentOfAuthor
from zds.tutorialv2.views.download_online import DownloadOnlineOpinion
from zds.tutorialv2.views.display import DisplayOnlineOpinion

urlpatterns = [
    # Flux
    re_path(r"^flux/rss/$", LastOpinionsFeedRSS(), name="feed-rss"),
    re_path(r"^flux/atom/$", LastOpinionsFeedATOM(), name="feed-atom"),
    # View
    re_path(r"^(?P<pk>\d+)/(?P<slug>.+)/$", DisplayOnlineOpinion.as_view(), name="view"),
    # downloads:
    re_path(
        r"^md/(?P<pk>\d+)/(?P<slug>.+)\.md$", DownloadOnlineOpinion.as_view(requested_file="md"), name="download-md"
    ),
    re_path(
        r"^html/(?P<pk>\d+)/(?P<slug>.+)\.html$",
        DownloadOnlineOpinion.as_view(requested_file="html"),
        name="download-html",
    ),
    re_path(
        r"^pdf/(?P<pk>\d+)/(?P<slug>.+)\.pdf$", DownloadOnlineOpinion.as_view(requested_file="pdf"), name="download-pdf"
    ),
    re_path(
        r"^epub/(?P<pk>\d+)/(?P<slug>.+)\.epub$",
        DownloadOnlineOpinion.as_view(requested_file="epub"),
        name="download-epub",
    ),
    re_path(
        r"^zip/(?P<pk>\d+)/(?P<slug>.+)\.zip$", DownloadOnlineOpinion.as_view(requested_file="zip"), name="download-zip"
    ),
    re_path(
        r"^tex/(?P<pk>\d+)/(?P<slug>.+)\.tex$", DownloadOnlineOpinion.as_view(requested_file="tex"), name="download-tex"
    ),
    # Listing
    re_path(r"^$", ListOpinions.as_view(), name="list"),
    path(
        "voir/<str:username>/",
        ContentOfAuthor.as_view(type="OPINION", context_object_name="opinions", sort="creation"),
        name="find-opinion",
    ),
]
