from django.conf.urls import url

from zds.utils.api.views import TagListAPI

urlpatterns = [
    url(r'^$', TagListAPI.as_view(), name='list'),
]
