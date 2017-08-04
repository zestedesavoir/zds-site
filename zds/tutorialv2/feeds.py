# coding: utf-8

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from zds.tutorialv2.models.models_database import PublishedContent


class LastContentFeedRSS(Feed):
    """
    RSS feed for any type of content.
    """
    title = _(u'Contenus sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _(u'Les derniers contenus parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])
    link = ''
    content_type = None

    def get_object(self, request, *args, **kwargs):
        self.query_params = request.GET
        return super(LastContentFeedRSS, self).get_object(request, *args, **kwargs)

    def items(self):
        """
        :return: The last (typically 5) contents (sorted by publication date).
        """
        categories = []
        if 'category' in self.query_params:
            categories = [self.query_params.get('category')]
        subcategories = []
        if 'subcategory' in self.query_params:
            subcategories = [self.query_params.get('subcategory')]

        feed_length = settings.ZDS_APP['content']['feed_length']

        contents = PublishedContent.objects.published_contents(
            _type=self.content_type,
            categories=categories,
            subcategories=subcategories
        )[:feed_length]

        return contents

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
        authors = ', '.join(authors)
        return authors

    def item_link(self, item):
        return item.get_absolute_url_online()


class LastContentFeedATOM(LastContentFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastContentFeedRSS.description


class LastTutorialsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for tutorials only
    """
    content_type = 'TUTORIAL'
    link = '/tutoriels/'
    title = _(u'Tutoriels sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _(u'Les derniers tutoriels parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])


class LastTutorialsFeedATOM(LastTutorialsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTutorialsFeedRSS.description


class LastArticlesFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for articles only
    """
    content_type = 'ARTICLE'
    link = '/articles/'
    title = _(u'Articles sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _(u'Les derniers articles parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastArticlesFeedRSS.description


class LastOpinionsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for opinions only
    """
    content_type = 'OPINION'
    link = '/tribunes/'
    title = _(u'Tribunes sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _(u'Les derniers billets des tribunes parus sur {}.').format(
        settings.ZDS_APP['site']['literal_name'])


class LastOpinionsFeedATOM(LastOpinionsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastOpinionsFeedRSS.description
