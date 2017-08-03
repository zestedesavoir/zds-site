# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.views.views_published import ViewAllCategories, ViewCategory, ViewSubCategory
from zds.tutorialv2.feeds import LastContentFeedRSS, LastContentFeedATOM

urlpatterns = [
    # Flux
    url(r'^flux/rss/$', LastContentFeedRSS(), name='feed-rss'),
    url(r'^flux/atom/$', LastContentFeedATOM(), name='feed-atom'),

    url(r'^(?P<slug_category>.+)/(?P<slug>.+)/$', ViewSubCategory.as_view(), name='subcategory'),
    url(r'^(?P<slug>.+)/$', ViewCategory.as_view(), name='category'),
    url(r'^$', ViewAllCategories.as_view(), name='list'),
]
