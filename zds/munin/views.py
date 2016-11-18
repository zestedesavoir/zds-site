from munin.helpers import muninview
from zds.forum.models import Topic, Post
from zds.mp.models import PrivateTopic, PrivatePost
from zds.tutorialv2.models.models_database import PublishableContent, ContentReaction
from django.db.models import Q


@muninview(config="""graph_title Total Topics
graph_vlabel topics""")
def total_topics(request):
    topics = Topic.objects.all()
    return [('topics', topics.count()),
            ('solved', topics.filter(is_solved=True).count())]


@muninview(config="""graph_title Total Posts
graph_vlabel posts
posts.label Forum posts
posts.draw LINE1
comments.label Article and Tutorial comments
comments.draw STACK""")
def total_posts(request):
    return [tuple(['posts', Post.objects.all().count()]),
            tuple(['comments', ContentReaction.objects.count()])]


@muninview(config="""graph_title Total MPs
graph_vlabel count""")
def total_mps(request):
    return [('mp', PrivateTopic.objects.all().count()),
            ('replies', PrivatePost.objects.all().count())]


@muninview(config="""graph_title Total Tutorials
graph_vlabel tutorials""")
def total_tutorials(request):
    tutorials = PublishableContent.objects.filter(type='TUTORIAL').all()
    return [('tutorials', tutorials.count()),
            ('offline', tutorials.filter(sha_public__isnull=True).count()),
            ('online', tutorials.filter(sha_public__isnull=False).count())]


@muninview(config="""graph_title Total articles
graph_vlabel articles""")
def total_articles(request):
    articles = PublishableContent.objects.filter(type='ARTICLE').all()
    return [('articles', articles.count()),
            ('offline', articles.filter(sha_public__isnull=True).count()),
            ('online', articles.filter(sha_public__isnull=False).count())]


@muninview(config="""graph_title Total Tribunes
graph_vlabel #tribunes
not_promoted.label Not published yet
not_promoted.draw LINE1
not_promoted.label Not promoted
not_promoted.draw STACK
promoted.label Promoted as articles
promoted.draw STACK""")
def total_tribunes(request):
    tribunes = PublishableContent.objects.filter(type='OPINION').all()
    return [('not_published', tribunes.filter(sha_public__isnull=True)),
            ('not_promoted', tribunes.filter(sha_public__isnull=False)
                                     .filter(Q(promotion_content__isnull=True) |
                                             Q(promotion_content__sha_public__isnull=True)).count()),
            ('promoted', tribunes.filter(promotion_content__sha_public__isnull=False).count())]
