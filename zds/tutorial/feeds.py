# coding: utf-8

from django.contrib.syndication.views import Feed
from django.conf import settings

from django.utils.feedgenerator import Atom1Feed

from .models import PubliableContent


class LastTutorialsFeedRSS(Feed):
    title = "Tutoriels sur {}".format(settings.ZDS_APP['site']['litteral_name'])
    link = "/tutoriels/"
    description = "Les derniers tutoriels parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])

    def items(self):
        return PubliableContent.objects\
            .filter(sha_public__isnull=False)\
            .order_by('-pubdate')[:5]

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.pubdate

    def item_description(self, item):
        return item.description

    def item_author_name(self, item):
        authors_list = item.authors.all()
        authors = []
        for authors_obj in authors_list:
            authors.append(authors_obj.username)
        authors = ", ".join(authors)
        return authors

    def item_link(self, item):
        return item.get_absolute_url()


class LastTutorialsFeedATOM(LastTutorialsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTutorialsFeedRSS.description
