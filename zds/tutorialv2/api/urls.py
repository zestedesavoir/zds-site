# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.api.views import ContentReactionKarmaView, ContentCast, VerbListFilteringView

urlpatterns = [
    url(r'^reactions/(?P<pk>\d+)/karma/?$', ContentReactionKarmaView.as_view(), name='reaction-karma'),
    url(r'^casting/$', ContentCast.as_view(), name='content-cast'),
    url(r'^verbs/$', VerbListFilteringView.as_view(), name='verb-search'),
    url(r'^items/$', VerbListFilteringView.as_view(), name='verb-search'),
]
