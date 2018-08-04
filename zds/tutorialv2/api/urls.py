from django.conf.urls import url

from zds.tutorialv2.api.views import ContentReactionKarmaView, ContainerPublicationReadinessView

urlpatterns = [
    url(r'^reactions/(?P<pk>\d+)/karma/?$', ContentReactionKarmaView.as_view(), name='reaction-karma'),
    url(r'^publication/preparation/(?P<pk>[0-9]+)/', ContainerPublicationReadinessView.as_view(), name='readiness')
]
