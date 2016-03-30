# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.api.views import ContentReactionKarmaView

urlpatterns = [
    url(r'^reactions/(?P<pk>\d+)/karma$', ContentReactionKarmaView.as_view(), name='api-content-reaction-karma'),
]
