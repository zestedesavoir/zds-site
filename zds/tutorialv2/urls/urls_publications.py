from django.urls import re_path

from zds.tutorialv2.views.published import ViewPublications
from zds.tutorialv2.feeds import LastContentFeedRSS, LastContentFeedATOM

urlpatterns = [
    # Flux
    re_path(r'^flux/rss/$', LastContentFeedRSS(), name='feed-rss'),
    re_path(r'^flux/atom/$', LastContentFeedATOM(), name='feed-atom'),
    re_path(r'^(?P<slug_category>.+)/(?P<slug>.+)/$',
            ViewPublications.as_view(), name='subcategory'),
    re_path(r'^(?P<slug>.+)/$', ViewPublications.as_view(), name='category'),
    re_path(r'^$', ViewPublications.as_view(), name='list'),
]
