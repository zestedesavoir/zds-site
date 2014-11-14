# coding: utf-8

from django.contrib.syndication.views import Feed

from django.utils.feedgenerator import Atom1Feed

from .models import Article


class LastArticlesFeedRSS(Feed):
    title = "Articles sur Zeste de Savoir"
    link = "/articles/"
    description = "Les derniers articles parus sur Zeste de Savoir."

    def items(self):
        return Article.objects\
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
        return item.get_absolute_url_online()


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastArticlesFeedRSS.description
