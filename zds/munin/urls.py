from django.urls import include, path

from zds.munin.views import (
    banned_users,
    total_articles,
    total_mps,
    total_opinions,
    total_posts,
    total_topics,
    total_tutorials,
)

urlpatterns = [
    path("", include(("django_munin.munin.urls", "base"))),
    path("banned_users/", banned_users, name="banned-users"),
    path("total_topics/", total_topics, name="total-topics"),
    path("total_posts/", total_posts, name="total-posts"),
    path("total_mps/", total_mps, name="total-mp"),
    path("total_tutorials/", total_tutorials, name="total-tutorial"),
    path("total_articles/", total_articles, name="total-articles"),
    path("total_opinions/", total_opinions, name="total-opinions"),
]
