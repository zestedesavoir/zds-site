from django.conf.urls import url

from .views import PostKarma

urlpatterns = [
    url(r'^message/(?P<pk>\d+)/karma$', PostKarma.as_view(), name='api-post-karma'),
]
