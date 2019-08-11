from django.urls import re_path

from zds.munin.views import total_topics, total_posts, total_mps, total_tutorials, total_articles, total_opinions


urlpatterns = [
    re_path(r'^total_topics/$', total_topics, name='total_topics'),
    re_path(r'^total_posts/$', total_posts, name='total_posts'),
    re_path(r'^total_mps/$', total_mps, name='total_mp'),
    re_path(r'^total_tutorials/$', total_tutorials, name='total_tutorial'),
    re_path(r'^total_articles/$', total_articles, name='total_articles'),
    re_path(r'^total_opinions/$', total_opinions, name='total_opinions'),
]
