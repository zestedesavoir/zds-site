from copy import deepcopy

from django.conf import settings
from django.http import Http404
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from zds.forum.tests.factories import TagFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.feeds import (
    LastArticlesFeedATOM,
    LastArticlesFeedRSS,
    LastOpinionsFeedATOM,
    LastOpinionsFeedRSS,
    LastTutorialsFeedATOM,
    LastTutorialsFeedRSS,
)
from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
)
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "NOTHING"


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
class LastTutorialsFeedsTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()
        self.tag = TagFactory()

        self.user_author = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.tags.add(self.tag)
        self.tuto.save()

        # fill it with one part, containing one chapter, containing one extract
        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

        # then, publish it !
        version = self.tuto_draft.current_version
        self.published = publish_content(self.tuto, self.tuto_draft, is_major_update=True)

        self.tuto.sha_public = version
        self.tuto.sha_draft = version
        self.tuto.public_version = self.published
        self.tuto.save()

        self.tutofeed = LastTutorialsFeedRSS()

    def test_is_well_setup(self):
        """Test that base parameters are Ok"""

        self.assertEqual(self.tutofeed.link, "/tutoriels/")
        reftitle = "Tutoriels sur {}".format(overridden_zds_app["site"]["literal_name"])
        self.assertEqual(self.tutofeed.title, reftitle)
        refdescription = "Les derniers tutoriels parus sur {}.".format(overridden_zds_app["site"]["literal_name"])
        self.assertEqual(self.tutofeed.description, refdescription)

        atom = LastTutorialsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """basic test sending back the tutorial"""

        ret = list(self.tutofeed.items())
        self.assertEqual(ret[0].content, self.tuto)

    def test_get_pubdate(self):
        """test the return value of pubdate"""

        ref = PublishedContent.objects.get(content__pk=self.tuto.pk).publication_date
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_pubdate(item=tuto)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """test the return value of title"""

        ref = self.tuto.title
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_title(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """test the return value of description"""

        ref = self.tuto.description
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_description(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """test the return value of author name"""

        ref = self.user_author.username
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_author_name(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """test the return value of item link"""

        ref = self.tuto.get_absolute_url_online()
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_link(item=tuto)
        self.assertEqual(ret, ref)

    def test_filters(self):
        """Test filtering by category & tag"""
        subcategory2 = SubCategoryFactory()
        subcategory3 = SubCategoryFactory()
        tag2 = TagFactory()
        tag3 = TagFactory()

        # Add a new tuto & publish it

        tuto2 = PublishableContentFactory(type="TUTORIAL")
        tuto2.authors.add(self.user_author)
        tuto2.licence = self.licence
        tuto2.subcategory.add(subcategory2)
        tuto2.tags.add(self.tag)
        tuto2.tags.add(tag2)
        tuto2.save()

        tuto2_draft = tuto2.load_version()
        tuto2.sha_public = tuto2.sha_draft = tuto2_draft.current_version
        tuto2.public_version = publish_content(tuto2, tuto2_draft, is_major_update=True)
        tuto2.save()

        # Default view

        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [tuto2, self.tuto])

        # Filter by subcategory

        self.tutofeed.query_params = {"subcategory": self.subcategory.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [self.tuto])

        self.tutofeed.query_params = {"subcategory": f" {self.subcategory.slug} "}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [self.tuto])

        self.tutofeed.query_params = {"subcategory": subcategory2.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [tuto2])

        self.tutofeed.query_params = {"subcategory": subcategory3.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [])

        self.tutofeed.query_params = {"subcategory": "invalid"}
        self.assertRaises(Http404, self.tutofeed.items)

        # Filter by tag

        self.tutofeed.query_params = {"tag": self.tag.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [tuto2, self.tuto])

        self.tutofeed.query_params = {"tag": tag2.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [tuto2])

        self.tutofeed.query_params = {"tag": f" {tag2.slug} "}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [tuto2])

        self.tutofeed.query_params = {"tag": tag3.slug}
        ret = [item.content for item in self.tutofeed.items()]
        self.assertEqual(ret, [])

        self.tutofeed.query_params = {"tag": "invalid"}
        self.assertRaises(Http404, self.tutofeed.items)

    def test_content_control_chars(self):
        """
        Test 'control characters' in content of the feed doesn't break it.

        The '\u0007' character in the post content belongs to a character
        family that is  not supported in RSS or Atom feeds and will break their
        generation.
        """
        buggy_tutorial = PublishedContentFactory(
            author_list=[self.user_author], type="TUTORIAL", description="Strange char: \u0007"
        )
        buggy_tutorial.subcategory.add(self.subcategory)
        buggy_tutorial.tags.add(self.tag)
        buggy_tutorial.save()

        request = self.client.get(reverse("tutorial:feed-rss"))
        self.assertEqual(request.status_code, 200)

        request = self.client.get(reverse("tutorial:feed-atom"))
        self.assertEqual(request.status_code, 200)


@override_settings(ZDS_APP=overridden_zds_app)
class LastArticlesFeedsTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()
        self.tag = TagFactory()

        self.user_author = ProfileFactory().user

        # create an article
        self.article = PublishableContentFactory(type="ARTICLE")
        self.article.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.article.gallery, user=self.user_author, mode="W")
        self.article.licence = self.licence
        self.article.subcategory.add(self.subcategory)
        self.article.tags.add(self.tag)
        self.article.save()

        # fill it with one extract
        self.article_draft = self.article.load_version()
        self.extract1 = ExtractFactory(container=self.article_draft, db_object=self.article)

        # then, publish it !
        version = self.article_draft.current_version
        self.published = publish_content(self.article, self.article_draft, is_major_update=True)

        self.article.sha_public = version
        self.article.sha_draft = version
        self.article.public_version = self.published
        self.article.save()

        self.articlefeed = LastArticlesFeedRSS()

    def test_is_well_setup(self):
        """Test that base parameters are Ok"""

        self.assertEqual(self.articlefeed.link, "/articles/")
        reftitle = "Articles sur {}".format(overridden_zds_app["site"]["literal_name"])
        self.assertEqual(self.articlefeed.title, reftitle)
        refdescription = "Les derniers articles parus sur {}.".format(overridden_zds_app["site"]["literal_name"])
        self.assertEqual(self.articlefeed.description, refdescription)

        atom = LastArticlesFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """basic test sending back the article"""

        ret = list(self.articlefeed.items())
        self.assertEqual(ret[0].content, self.article)

    def test_get_pubdate(self):
        """test the return value of pubdate"""

        ref = PublishedContent.objects.get(content__pk=self.article.pk).publication_date
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_pubdate(item=article)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """test the return value of title"""

        ref = self.article.title
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_title(item=article)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """test the return value of description"""

        ref = self.article.description
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_description(item=article)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """test the return value of author name"""

        ref = self.user_author.username
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_author_name(item=article)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """test the return value of item link"""

        ref = self.article.get_absolute_url_online()
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_link(item=article)
        self.assertEqual(ret, ref)

    def test_filters(self):
        """Test filtering by category & tag"""
        subcategory2 = SubCategoryFactory()
        subcategory3 = SubCategoryFactory()
        tag2 = TagFactory()
        tag3 = TagFactory()

        # Add a new tuto & publish it

        article2 = PublishableContentFactory(type="ARTICLE")
        article2.authors.add(self.user_author)
        article2.licence = self.licence
        article2.subcategory.add(subcategory2)
        article2.tags.add(self.tag)
        article2.tags.add(tag2)
        article2.save()

        article2_draft = article2.load_version()
        article2.sha_public = article2.sha_draft = article2_draft.current_version
        article2.public_version = publish_content(article2, article2_draft, is_major_update=True)
        article2.save()

        # Default view

        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [article2, self.article])

        # Filter by subcategory

        self.articlefeed.query_params = {"subcategory": self.subcategory.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [self.article])

        self.articlefeed.query_params = {"subcategory": f" {self.subcategory.slug} "}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [self.article])

        self.articlefeed.query_params = {"subcategory": subcategory2.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [article2])

        self.articlefeed.query_params = {"subcategory": subcategory3.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [])

        self.articlefeed.query_params = {"subcategory": "invalid"}
        self.assertRaises(Http404, self.articlefeed.items)

        # Filter by tag

        self.articlefeed.query_params = {"tag": self.tag.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [article2, self.article])

        self.articlefeed.query_params = {"tag": tag2.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [article2])

        self.articlefeed.query_params = {"tag": f" {tag2.slug} "}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [article2])

        self.articlefeed.query_params = {"tag": tag3.slug}
        ret = [item.content for item in self.articlefeed.items()]
        self.assertEqual(ret, [])

        self.articlefeed.query_params = {"tag": "invalid"}
        self.assertRaises(Http404, self.articlefeed.items)

    def test_content_control_chars(self):
        """
        Test 'control characters' in content of the feed doesn't break it.

        The '\u0007' character in the post content belongs to a character
        family that is  not supported in RSS or Atom feeds and will break their
        generation.
        """
        buggy_article = PublishedContentFactory(
            author_list=[self.user_author], type="ARTICLE", description="Strange char: \u0007"
        )
        buggy_article.subcategory.add(self.subcategory)
        buggy_article.tags.add(self.tag)
        buggy_article.save()

        request = self.client.get(reverse("article:feed-rss"))
        self.assertEqual(request.status_code, 200)

        request = self.client.get(reverse("article:feed-atom"))
        self.assertEqual(request.status_code, 200)


@override_settings(ZDS_APP=overridden_zds_app)
class LastOpinionsFeedsTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app

        self.subcategory = SubCategoryFactory()
        self.tag = TagFactory()
        self.user_author = ProfileFactory().user

        # create an opinion
        self.opinion = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        self.opinion.subcategory.add(self.subcategory)
        self.opinion.tags.add(self.tag)
        self.opinion.save()

        self.opinionfeed = LastOpinionsFeedRSS()

    def test_is_well_setup(self):
        """Test that base parameters are Ok"""

        self.assertEqual(self.opinionfeed.link, "/tribunes/")
        reftitle = "Tribunes sur {}".format(overridden_zds_app["site"]["literal_name"])
        self.assertEqual(self.opinionfeed.title, reftitle)
        refdescription = "Les derniers billets des tribunes parus sur {}.".format(
            overridden_zds_app["site"]["literal_name"]
        )
        self.assertEqual(self.opinionfeed.description, refdescription)

        atom = LastOpinionsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """basic test sending back the article"""

        ret = list(self.opinionfeed.items())
        self.assertEqual(ret[0].content, self.opinion)

    def test_get_pubdate(self):
        """test the return value of pubdate"""

        ref = PublishedContent.objects.get(content__pk=self.opinion.pk).publication_date
        opinion = list(self.opinionfeed.items())[0]
        ret = self.opinionfeed.item_pubdate(item=opinion)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """test the return value of title"""

        ref = self.opinion.title
        opinion = list(self.opinionfeed.items())[0]
        ret = self.opinionfeed.item_title(item=opinion)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """test the return value of description"""

        ref = self.opinion.description
        opinion = list(self.opinionfeed.items())[0]
        ret = self.opinionfeed.item_description(item=opinion)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """test the return value of author name"""

        ref = self.user_author.username
        opinion = list(self.opinionfeed.items())[0]
        ret = self.opinionfeed.item_author_name(item=opinion)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """test the return value of item link"""

        ref = self.opinion.get_absolute_url_online()
        opinion = list(self.opinionfeed.items())[0]
        ret = self.opinionfeed.item_link(item=opinion)
        self.assertEqual(ret, ref)

    def test_filters(self):
        """Test filtering by category & tag"""
        subcategory2 = SubCategoryFactory()
        subcategory3 = SubCategoryFactory()
        tag2 = TagFactory()
        tag3 = TagFactory()

        # Add a new opinion & publish it

        opinion2 = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        opinion2.subcategory.add(subcategory2)
        opinion2.tags.add(self.tag)
        opinion2.tags.add(tag2)
        opinion2.save()

        # Default view

        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [opinion2, self.opinion])

        # Filter by subcategory

        self.opinionfeed.query_params = {"subcategory": self.subcategory.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [self.opinion])

        self.opinionfeed.query_params = {"subcategory": f" {self.subcategory.slug} "}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [self.opinion])

        self.opinionfeed.query_params = {"subcategory": subcategory2.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [opinion2])

        self.opinionfeed.query_params = {"subcategory": subcategory3.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [])

        self.opinionfeed.query_params = {"subcategory": "invalid"}
        self.assertRaises(Http404, self.opinionfeed.items)

        # Filter by tag

        self.opinionfeed.query_params = {"tag": self.tag.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [opinion2, self.opinion])

        self.opinionfeed.query_params = {"tag": tag2.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [opinion2])

        self.opinionfeed.query_params = {"tag": f" {tag2.slug} "}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [opinion2])

        self.opinionfeed.query_params = {"tag": tag3.slug}
        ret = [item.content for item in self.opinionfeed.items()]
        self.assertEqual(ret, [])

        self.opinionfeed.query_params = {"tag": "invalid"}
        self.assertRaises(Http404, self.opinionfeed.items)

    def test_content_control_chars(self):
        """
        Test 'control characters' in content of the feed doesn't break it.

        The '\u0007' character in the post content belongs to a character
        family that is  not supported in RSS or Atom feeds and will break their
        generation.
        """
        buggy_opinion = PublishedContentFactory(
            author_list=[self.user_author], type="OPINION", description="Strange char: \u0007"
        )
        buggy_opinion.subcategory.add(self.subcategory)
        buggy_opinion.tags.add(self.tag)
        buggy_opinion.save()

        request = self.client.get(reverse("opinion:feed-rss"))
        self.assertEqual(request.status_code, 200)

        request = self.client.get(reverse("opinion:feed-atom"))
        self.assertEqual(request.status_code, 200)
