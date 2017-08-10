from django.conf.urls import url

from zds.tutorialv2.api.views import ContentReactionKarmaView

urlpatterns = [
    url(r'^reactions/(?P<pk>\d+)/karma/?$', ContentReactionKarmaView.as_view(), name='reaction-karma'),
]
