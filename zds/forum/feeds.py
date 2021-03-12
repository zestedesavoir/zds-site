from django.contrib.syndication.views import Feed

from django.utils.feedgenerator import Atom1Feed
from django.conf import settings

from .models import Post, Topic


class ItemMixin:
    def item_pubdate(self, item):
        return item.pubdate

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


def request_object(request):
    obj = {}
    if "forum" in request.GET:
        obj["forum"] = request.GET["forum"]
    if "tag" in request.GET:
        obj["tag"] = request.GET["tag"]
    return obj


class LastPostsFeedRSS(Feed, ItemMixin):
    title = "Derniers messages sur {}".format(settings.ZDS_APP["site"]["literal_name"])
    link = "/forums/"
    description = "Les derniers messages " "parus sur le forum de {}.".format(settings.ZDS_APP["site"]["literal_name"])

    def get_object(self, request):
        return request_object(request)

    def items(self, obj):
        try:
            posts = Post.objects.filter(topic__forum__groups__isnull=True)
            if "forum" in obj:
                posts = posts.filter(topic__forum__pk=int(obj["forum"]))
            if "tag" in obj:
                posts = posts.filter(topic__tags__pk__in=[obj["tag"]])
            posts = posts.order_by("-pubdate")[: settings.ZDS_APP["forum"]["posts_per_page"]]
        except (Post.DoesNotExist, ValueError):
            posts = []
        return posts

    def item_title(self, item):
        return f"{item.topic.title}, message #{item.pk}"

    def item_description(self, item):
        return item.text_html


class LastPostsFeedATOM(LastPostsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastPostsFeedRSS.description


class LastTopicsFeedRSS(Feed, ItemMixin):
    title = "Derniers sujets sur {}".format(settings.ZDS_APP["site"]["literal_name"])
    link = "/forums/"
    description = "Les derniers sujets créés sur le forum de {}.".format(settings.ZDS_APP["site"]["literal_name"])

    def get_object(self, request):
        return request_object(request)

    def items(self, obj):
        try:
            topics = Topic.objects.filter(forum__groups__isnull=True)
            if "forum" in obj:
                topics = topics.filter(forum__pk=int(obj["forum"]))
            if "tag" in obj:
                topics = topics.filter(tags__pk__in=[obj["tag"]])
            topics = topics.order_by("-pubdate")[: settings.ZDS_APP["forum"]["posts_per_page"]]
        except (Topic.DoesNotExist, ValueError):
            topics = []
        return topics

    def item_title(self, item):
        return f"{item.title} dans {item.forum.title}"

    def item_description(self, item):
        return item.subtitle


class LastTopicsFeedATOM(LastTopicsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTopicsFeedRSS.description
