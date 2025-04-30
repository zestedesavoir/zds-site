from django.conf import settings
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _
from pytz import AmbiguousTimeError, NonExistentTimeError

from zds.tutorialv2.models.database import PublishedContent
from zds.utils.feeds import DropControlCharsAtom1Feed, DropControlCharsRss201rev2Feed
from zds.utils.models import Category, SubCategory, Tag
from zds.utils.uuslug_wrapper import slugify


class LastContentFeedRSS(Feed):
    """
    RSS feed for any type of content.
    """

    title = _("Contenus sur {}").format(settings.ZDS_APP["site"]["literal_name"])
    description = _("Les derniers contenus parus sur {}.").format(settings.ZDS_APP["site"]["literal_name"])
    link = ""
    content_type = None
    query_params = {}
    feed_type = DropControlCharsRss201rev2Feed

    def get_object(self, request, *args, **kwargs):
        self.query_params = request.GET
        return super().get_object(request, *args, **kwargs)

    def items(self):
        """
        :return: The last (typically 5) contents (sorted by publication date).
        """
        subcategories = None
        category = self.query_params.get("category", "").strip()
        if category:
            category = get_object_or_404(Category, slug=category)
            subcategories = category.get_subcategories()
        subcategory = self.query_params.get("subcategory", "").strip()
        if subcategory:
            subcategories = [get_object_or_404(SubCategory, slug=subcategory)]

        tags = None
        tag = self.query_params.get("tag", "").strip()
        if tag:
            tags = [get_object_or_404(Tag, slug=slugify(self.query_params.get("tag")))]

        feed_length = settings.ZDS_APP["content"]["feed_length"]

        contents = PublishedContent.objects.last_contents(
            content_type=[self.content_type], subcategories=subcategories, tags=tags
        )[:feed_length]

        return contents

    def item_title(self, item):
        return item.content.title

    def item_pubdate(self, item):
        try:
            return make_aware(item.publication_date)
        except AmbiguousTimeError:
            try:
                return make_aware(item.publication_date, is_dst=True)
            except NonExistentTimeError:
                return make_aware(item.publication_date, is_dst=False)

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


class LastContentFeedATOM(LastContentFeedRSS):
    feed_type = DropControlCharsAtom1Feed
    subtitle = LastContentFeedRSS.description


class LastTutorialsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for tutorials only
    """

    content_type = "TUTORIAL"
    link = "/tutoriels/"
    title = _("Tutoriels sur {}").format(settings.ZDS_APP["site"]["literal_name"])
    description = _("Les derniers tutoriels parus sur {}.").format(settings.ZDS_APP["site"]["literal_name"])


class LastTutorialsFeedATOM(LastTutorialsFeedRSS):
    feed_type = DropControlCharsAtom1Feed
    subtitle = LastTutorialsFeedRSS.description


class LastArticlesFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for articles only
    """

    content_type = "ARTICLE"
    link = "/articles/"
    title = _("Articles sur {}").format(settings.ZDS_APP["site"]["literal_name"])
    description = _("Les derniers articles parus sur {}.").format(settings.ZDS_APP["site"]["literal_name"])


class LastArticlesFeedATOM(LastArticlesFeedRSS):
    feed_type = DropControlCharsAtom1Feed
    subtitle = LastArticlesFeedRSS.description


class LastOpinionsFeedRSS(LastContentFeedRSS):
    """
    Redefinition of `LastContentFeedRSS` for opinions only
    """

    content_type = "OPINION"
    link = "/tribunes/"
    title = _("Tribunes sur {}").format(settings.ZDS_APP["site"]["literal_name"])
    description = _("Les derniers billets des tribunes parus sur {}.").format(settings.ZDS_APP["site"]["literal_name"])


class LastOpinionsFeedATOM(LastOpinionsFeedRSS):
    feed_type = DropControlCharsAtom1Feed
    subtitle = LastOpinionsFeedRSS.description
