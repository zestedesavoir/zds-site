# coding: utf-8

from django.contrib.syndication.views import Feed
from django.conf import settings

from django.utils.feedgenerator import Atom1Feed

from zds.tutorialv2.models.models_database import PublishedContent
from zds.settings import ZDS_APP


class LastContentFeedRSS(Feed):
    """
    RSS feed for any type of content.
    """
    title = u"Contenu sur {}".format(settings.ZDS_APP['site']['litteral_name'])
    description = u"Les derniers contenus parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])
    link = ""
    content_type = None

    def items(self):
        """
        :return: The last (typically 5) contents (sorted by publication date).
        If `self.type` is not `None`, the contents will only be of this type.
        """
        contents = PublishedContent.objects.published()\
            .prefetch_related("content")\
            .prefetch_related("content__authors")

        if self.content_type is not None:
            contents = contents.filter(content_type=self.content_type)

        return contents.order_by('-publication_date')[:ZDS_APP['content']['feed_length']]

    def item_title(self, item):
        return item.content.title

    def item_pubdate(self, item):
        return item.publication_date

    def item_description(self, item):
        return item.content.description

    def item_author_name(self, item):
        authors_list = item.content.authors.all()
        authors = []
        for authors_obj in authors_list:
            authors.append(authors_obj.username)
        authors = ", ".join(authors)
        return authors

    def item_link(self, item):
        return item.get_absolute_url_online()


class LastTutorialsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for tutorials only
    """
    content_type = "TUTORIAL"
    link = "/tutoriels/"
    title = u"Tutoriels sur {}".format(settings.ZDS_APP['site']['litteral_name'])
    description = u"Les derniers tutoriels parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])


class LastTutorialsFeedATOM(LastTutorialsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTutorialsFeedRSS.description


class LastArticlesFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for articles only
    """
    content_type = "ARTICLE"
    link = "/articles/"
    title = u"Articles sur {}".format(settings.ZDS_APP['site']['litteral_name'])
    description = u"Les derniers articles parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastArticlesFeedRSS.description
