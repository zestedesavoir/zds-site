from django.conf import settings
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from zds.utils.models import Category, SubCategory
from zds.tutorialv2.models.database import PublishedContent


class LastContentFeedRSS(Feed):
    """
    RSS feed for any type of content.
    """
    title = _('Contenus sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _('Les derniers contenus parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])
    link = ''
    content_type = None
    query_params = {}

    def get_object(self, request, *args, **kwargs):
        self.query_params = request.GET
        return super(LastContentFeedRSS, self).get_object(request, *args, **kwargs)

    def items(self):
        """
        :return: The last (typically 5) contents (sorted by publication date).
        """
        subcategories = None
        if 'category' in self.query_params:
            category = get_object_or_404(Category, slug=self.query_params.get('category'))
            subcategories = category.get_subcategories()
        if 'subcategory' in self.query_params:
            subcategories = [get_object_or_404(SubCategory, slug=self.query_params.get('subcategory'))]

        feed_length = settings.ZDS_APP['content']['feed_length']

        contents = PublishedContent.objects.last_contents(
            content_type=[self.content_type],
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
    title = _('Tutoriels sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _('Les derniers tutoriels parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])


class LastTutorialsFeedATOM(LastTutorialsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTutorialsFeedRSS.description


class LastArticlesFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for articles only
    """
    content_type = 'ARTICLE'
    link = '/articles/'
    title = _('Articles sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _('Les derniers articles parus sur {}.').format(settings.ZDS_APP['site']['literal_name'])


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastArticlesFeedRSS.description


class LastOpinionsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for opinions only
    """
    content_type = 'OPINION'
    link = '/tribunes/'
    title = _('Tribunes sur {}').format(settings.ZDS_APP['site']['literal_name'])
    description = _('Les derniers billets des tribunes parus sur {}.').format(
        settings.ZDS_APP['site']['literal_name'])


class LastOpinionsFeedATOM(LastOpinionsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastOpinionsFeedRSS.description
