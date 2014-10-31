from munin.helpers import muninview
from zds.forum.models import Topic, Post
from zds.mp.models import PrivateTopic, PrivatePost
from zds.tutorial.models import PubliableContent
from zds.article.models import Article


@muninview(config="""graph_title Total Topics
graph_vlabel topics""")
def total_topics(request):
    topics = Topic.objects.all()
    return [("topics", topics.count()),
            ("solved", topics.filter(is_solved=True).count())]


@muninview(config="""graph_title Total Posts
graph_vlabel posts""")
def total_posts(request):
    return [("posts", Post.objects.all().count())]


@muninview(config="""graph_title Total MPs
graph_vlabel count""")
def total_mps(request):
    return [("mp", PrivateTopic.objects.all().count()),
            ("replies", PrivatePost.objects.all().count())]


@muninview(config="""graph_title Total Tutorials
graph_vlabel tutorials""")
def total_tutorials(request):
    tutorials = PubliableContent.objects.all()
    return [("tutorials", tutorials.count()),
            ("offline", tutorials.filter(sha_public__isnull=True).count()),
            ("online", tutorials.filter(sha_public__isnull=False).count())]


@muninview(config="""graph_title Total articles
graph_vlabel articles""")
def total_articles(request):
    articles = Article.objects.all()
    return [("articles", articles.count()),
            ("offline", articles.filter(sha_public__isnull=True).count()),
            ("online", articles.filter(sha_public__isnull=False).count())]
