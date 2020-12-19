from django.urls import re_path

from zds.forum.api.views import PostKarmaView

urlpatterns = [
    re_path(r"^message/(?P<pk>\d+)/karma/?$", PostKarmaView.as_view(), name="post-karma"),
]
