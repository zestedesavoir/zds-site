from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from .models import Article


class LastArticlesFeedRSS(Feed):
    title = "Articles sur Progdupeupl"
    link = "/articles/"
    description = "Les derniers articles parus sur Progdupeupl."

    def items(self):
        return Article.objects\
            .filter(is_visible=True)\
            .order_by('-pubdate')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastArticlesFeedRSS.description
