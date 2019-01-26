from django.conf.urls import url

from zds.tutorialv2.views.published import ViewPublications
from zds.tutorialv2.feeds import LastContentFeedRSS, LastContentFeedATOM

urlpatterns = [
    # Flux
    url(r'^flux/rss/$', LastContentFeedRSS(), name='feed-rss'),
    url(r'^flux/atom/$', LastContentFeedATOM(), name='feed-atom'),
    url(r'^(?P<slug_category>.+)/(?P<slug>.+)/$', ViewPublications.as_view(), name='subcategory'),
    url(r'^(?P<slug>.+)/$', ViewPublications.as_view(), name='category'),
    url(r'^$', ViewPublications.as_view(), name='list'),
]
