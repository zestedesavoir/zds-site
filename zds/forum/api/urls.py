from django.conf.urls import url

from .views import PostKarmaView

urlpatterns = [
    url(r'^message/(?P<pk>\d+)/karma/?$', PostKarmaView.as_view(), name='post-karma'),
]
