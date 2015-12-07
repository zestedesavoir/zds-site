# -*- coding: utf-8 -*-:

from django.conf.urls import url

from zds.munin.views import total_topics, total_posts, total_mps, total_tutorials, total_articles


urlpatterns = [
    url(r'^total_topics/$', total_topics),
    url(r'^total_posts/$', total_posts),
    url(r'^total_mps/$', total_mps),
    url(r'^total_tutorials/$', total_tutorials),
    url(r'^total_articles/$', total_articles),
]
