from django.urls import re_path

from zds.tutorialv2.api.views import ContentReactionKarmaView, ContainerPublicationReadinessView

urlpatterns = [
    re_path(r'^reactions/(?P<pk>\d+)/karma/?$',
            ContentReactionKarmaView.as_view(), name='reaction-karma'),
    re_path(r'^publication/preparation/(?P<pk>[0-9]+)/',
            ContainerPublicationReadinessView.as_view(), name='readiness')
]
