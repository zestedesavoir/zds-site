from django.urls import path, re_path
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.contributors import ContentOfContributors
from zds.tutorialv2.views.lists import TagsListView, ContentOfAuthor
from zds.tutorialv2.views.download_online import DownloadOnlineArticle
from zds.tutorialv2.views.display import DisplayOnlineArticle
from zds.tutorialv2.feeds import LastArticlesFeedRSS, LastArticlesFeedATOM

urlpatterns = [
    # Flux
    path("flux/rss/", LastArticlesFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastArticlesFeedATOM(), name="feed-atom"),
    # View
    path("<int:pk>/<slug:slug>/", DisplayOnlineArticle.as_view(), name="view"),
    # Downloads
    path("md/<int:pk>/<slug:slug>.md", DownloadOnlineArticle.as_view(requested_file="md"), name="download-md"),
    path(
        "html/<int:pk>/<slug:slug>.html",
        DownloadOnlineArticle.as_view(requested_file="html"),
        name="download-html",
    ),
    path("pdf/<int:pk>/<slug:slug>.pdf", DownloadOnlineArticle.as_view(requested_file="pdf"), name="download-pdf"),
    path("tex/<int:pk>/<slug:slug>.tex", DownloadOnlineArticle.as_view(requested_file="tex"), name="download-tex"),
    path(
        "epub/<int:pk>/<slug:slug>.epub",
        DownloadOnlineArticle.as_view(requested_file="epub"),
        name="download-epub",
    ),
    path("zip/<int:pk>/<slug:slug>.zip", DownloadOnlineArticle.as_view(requested_file="zip"), name="download-zip"),
    # Listing
    path("", RedirectView.as_view(pattern_name="publication:list", permanent=True)),
    re_path(r"tags/*", TagsListView.as_view(displayed_types=["ARTICLE"]), name="tags"),
    path(
        "voir/<str:username>/",
        ContentOfAuthor.as_view(type="ARTICLE", context_object_name="articles"),
        name="find-article",
    ),
    path(
        "contributions/<str:username>/",
        ContentOfContributors.as_view(type="ARTICLE", context_object_name="contribution_articles"),
        name="find-contributions-article",
    ),
]
