from django.conf.urls import url

from zds.munin.views import total_topics, total_posts, total_mps, total_tutorials, total_articles, total_opinions


urlpatterns = [
    url(r'^total_topics/$', total_topics, name='total_topics'),
    url(r'^total_posts/$', total_posts, name='total_posts'),
    url(r'^total_mps/$', total_mps, name='total_mp'),
    url(r'^total_tutorials/$', total_tutorials, name='total_tutorial'),
    url(r'^total_articles/$', total_articles, name='total_articles'),
    url(r'^total_opinions/$', total_opinions, name='total_opinions'),
]
