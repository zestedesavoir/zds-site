from django.urls import path

from zds.munin.views import total_topics, total_posts, total_mps, total_tutorials, total_articles, total_opinions


urlpatterns = [
    path("total_topics/", total_topics, name="total_topics"),
    path("total_posts/", total_posts, name="total_posts"),
    path("total_mps/", total_mps, name="total_mp"),
    path("total_tutorials/", total_tutorials, name="total_tutorial"),
    path("total_articles/", total_articles, name="total_articles"),
    path("total_opinions/", total_opinions, name="total_opinions"),
]
