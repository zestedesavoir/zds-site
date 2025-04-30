from django.urls import path

from zds.tutorialv2.feeds import LastContentFeedATOM, LastContentFeedRSS
from zds.tutorialv2.views.lists import ViewPublications

urlpatterns = [
    # Flux
    path("flux/rss/", LastContentFeedRSS(), name="feed-rss"),
    path("flux/atom/", LastContentFeedATOM(), name="feed-atom"),
    path("<slug:slug_category>/<slug:slug>/", ViewPublications.as_view(), name="subcategory"),
    path("<slug:slug>/", ViewPublications.as_view(), name="category"),
    path("", ViewPublications.as_view(), name="list"),
]
