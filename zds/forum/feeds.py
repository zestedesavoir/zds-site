# coding: utf-8

from django.contrib.syndication.views import Feed

from django.utils.feedgenerator import Atom1Feed
from django.conf import settings

from zds.utils.templatetags.emarkdown import emarkdown

from .models import Post, Topic


class LastPostsFeedRSS(Feed):
    title = u'Derniers messages sur {}'.format(settings.ZDS_APP['site']['litteral_name'])
    link = '/forums/'
    description = (u'Les derniers messages '
                   u'parus sur le forum de {}.'.format(settings.ZDS_APP['site']['litteral_name']))

    def get_object(self, request):
        obj = {}
        if 'forum' in request.GET:
            obj['forum'] = request.GET['forum']
        if 'tag' in request.GET:
            obj['tag'] = request.GET['tag']
        return obj

    def items(self, obj):
        try:
            posts = Post.objects.filter(topic__forum__group__isnull=True)
            if 'forum' in obj and 'tag' in obj:
                posts = posts.filter(topic__forum__pk=int(obj['forum']))
            if 'tag' in obj:
                posts = posts.filter(topic__tags__pk__in=[obj['tag']])
            posts = posts.order_by('-pubdate')[:settings.ZDS_APP['forum']['posts_per_page']]
        except (Post.DoesNotExist, ValueError):
            posts = []
        return posts

    def item_title(self, item):
        return u'{}, message #{}'.format(item.topic.title, item.pk)

    def item_pubdate(self, item):
        return item.pubdate

    def item_description(self, item):
        return item.html_text

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
    title = u'Derniers sujets sur {}'.format(settings.ZDS_APP['site']['litteral_name'])
    link = '/forums/'
    description = u'Les derniers sujets créés sur le forum de {}.'.format(settings.ZDS_APP['site']['litteral_name'])

    def get_object(self, request):
        obj = {}
        if 'forum' in request.GET:
            obj['forum'] = request.GET['forum']
        if 'tag' in request.GET:
            obj['tag'] = request.GET['tag']
        return obj

    def items(self, obj):
        try:
            topics = Topic.objects.filter(forum__group__isnull=True)
            if 'forum' in obj:
                topics = topics.filter(forum__pk=int(obj['forum']))
            if 'tag' in obj:
                topics = topics.filter(tags__pk__in=[obj['tag']])
            topics = topics.order_by('-pubdate')[:settings.ZDS_APP['forum']['posts_per_page']]
        except (Topic.DoesNotExist, ValueError):
            topics = []
        return topics

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
