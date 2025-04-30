from django_munin.munin.helpers import muninview
from zds.forum.models import Post, Topic
from zds.member.models import Profile
from zds.mp.models import PrivatePost, PrivateTopic
from zds.tutorialv2.models.database import ContentReaction, PublishableContent


@muninview(
    config="""graph_title Banned Users
graph_vlabel Banned Users
graph_args --lower-limit 0
graph_scale no"""
)
def banned_users(request):
    return [("banned_users", Profile.objects.filter(can_read=False, end_ban_read=None).count())]


@muninview(
    config="""graph_title Total Topics
graph_vlabel topics"""
)
def total_topics(request):
    topics = Topic.objects.all()
    return [("topics", topics.count()), ("solved", topics.filter(solved_by__isnull=False).count())]


@muninview(
    config="""graph_title Total Posts
graph_vlabel posts
posts.label Forum posts
posts.draw LINE1
comments.label Article and Tutorial comments
comments.draw STACK"""
)
def total_posts(request):
    return [tuple(["posts", Post.objects.all().count()]), tuple(["comments", ContentReaction.objects.count()])]


@muninview(
    config="""graph_title Total MPs
graph_vlabel count"""
)
def total_mps(request):
    return [("mp", PrivateTopic.objects.all().count()), ("replies", PrivatePost.objects.all().count())]


@muninview(
    config="""graph_title Total Tutorials
graph_vlabel tutorials"""
)
def total_tutorials(request):
    tutorials = PublishableContent.objects.filter(type="TUTORIAL").all()
    return [
        ("tutorials", tutorials.count()),
        ("offline", tutorials.filter(sha_public__isnull=True).count()),
        ("online", tutorials.filter(sha_public__isnull=False).count()),
    ]


@muninview(
    config="""graph_title Total articles
graph_vlabel articles"""
)
def total_articles(request):
    articles = PublishableContent.objects.filter(type="ARTICLE").all()
    return [
        ("articles", articles.count()),
        ("offline", articles.filter(sha_public__isnull=True).count()),
        ("online", articles.filter(sha_public__isnull=False).count()),
    ]


@muninview(
    config="""graph_title Total Opinions
graph_vlabel #opinions
draft.label Draft
draft.draw LINE1
featured.label Featured
published.label Published
converted.label Converted
"""
)
def total_opinions(request):
    opinions = PublishableContent.objects.filter(type="OPINION").all()
    return [
        ("draft", opinions.filter(sha_public__isnull=True).count()),
        ("featured", opinions.filter(sha_picked__isnull=False).count()),
        ("published", opinions.filter(sha_public__isnull=False).count()),
        ("converted", opinions.filter(converted_to__sha_public__isnull=False).count()),
    ]
