# coding: utf-8

from django.contrib.syndication.views import Feed

from django.utils.feedgenerator import Atom1Feed
from django.conf import settings

from zds.utils.templatetags.emarkdown import emarkdown

from .models import Post, Topic


class LastPostsFeedRSS(Feed):
    title = u'Derniers messages sur Zeste de Savoir'
    link = '/forums/'
    description = (u'Les derniers messages '
        u'parus sur le forum de Zeste de Savoir.')
    
    def get_object(self, request):
        obj = {}
        if "forum" in request.GET:
            obj['forum']=request.GET["forum"]
        if "tag" in request.GET:
            obj['tag']=request.GET["tag"]
        return obj

    def items(self, obj):
        if "forum" in obj and "tag" in obj:
            posts = Post.objects.filter(topic__forum__group__isnull=True,
                                        topic__forum__pk=obj['forum'],
                                        topic__tags__pk__in=[obj['tag']])\
            .order_by('-pubdate')
        elif "forum" in obj and "tag" not in obj:
            posts = Post.objects.filter(topic__forum__group__isnull=True,
                                        topic__forum__pk=obj['forum'])\
            .order_by('-pubdate')
        elif "forum" not in obj and "tag" in obj:
            posts = Post.objects.filter(topic__forum__group__isnull=True,
                                        topic__tags__pk__in=[obj['tag']])\
            .order_by('-pubdate')
        if "forum" not in obj and "tag" not in obj:
            posts = Post.objects.filter(topic__forum__group__isnull=True)\
                .order_by('-pubdate')

        return posts[:settings.POSTS_PER_PAGE]

    def item_title(self, item):
        return u'{}, message #{}'.format(item.topic.title, item.pk)

    def item_pubdate(self, item):
        return item.pubdate

    def item_description(self, item):
        # TODO: Use cached Markdown when implemented
        return emarkdown(item.text)

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


class LastPostsFeedATOM(LastPostsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastPostsFeedRSS.description


class LastTopicsFeedRSS(Feed):
    title = u'Derniers sujets sur Zeste de Savoir'
    link = '/forums/'
    description = u'Les derniers sujets créés sur le forum de Zeste de Savoir.'
    
    def get_object(self, request):
        obj = {}
        if "forum" in request.GET:
            obj['forum']=request.GET["forum"]
        if "tag" in request.GET:
            obj['tag']=request.GET["tag"]
        return obj

    def items(self, obj):
        if "forum" in obj and "tag" in obj:
            topics = Topic.objects.filter(forum__group__isnull=True,
                                          forum__pk=obj['forum'],
                                          tags__pk__in=[obj['tag']])\
            .order_by('-pubdate')
        elif "forum" in obj and "tag" not in obj:
            topics = Topic.objects.filter(forum__group__isnull=True,
                                          forum__pk=obj['forum'])\
            .order_by('-pubdate')
        elif "forum" not in obj and "tag" in obj:
            topics = Topic.objects.filter(forum__group__isnull=True,
                                          tags__pk__in=[obj['tag']])\
            .order_by('-pubdate')
        if "forum" not in obj and "tag" not in obj:
            topics = Topic.objects.filter(forum__group__isnull=True)\
                .order_by('-pubdate')

        return topics[:settings.POSTS_PER_PAGE]
    def item_pubdate(self, item):
        return item.pubdate

    def item_title(self, item):
        return u'{} dans {}'.format(item.title, item.forum.title)

    def item_description(self, item):
        return item.subtitle

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


class LastTopicsFeedATOM(LastTopicsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTopicsFeedRSS.description
