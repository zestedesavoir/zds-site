from django.urls import re_path

from zds.utils.api.views import TagListAPI

urlpatterns = [
    re_path(r'^$', TagListAPI.as_view(), name='list'),
]
