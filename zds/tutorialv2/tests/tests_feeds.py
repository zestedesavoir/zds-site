from django.conf import settings
from django.http import Http404
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import Group

from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.forum.tests.factories import ForumFactory, ForumCategoryFactory, TagFactory
from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM, LastArticlesFeedRSS, LastArticlesFeedATOM
from zds.tutorialv2.factories import (
    PublishableContentFactory,
    ContainerFactory,
    ExtractFactory,
)
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from zds.utils.factories import SubCategoryFactory, LicenceFactory
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
class LastTutorialsFeedRSSTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app["content"]["build_pdf_when_published"] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        overridden_zds_app["member"]["bot_account"] = self.mas.username

        bot = Group(name=overridden_zds_app["member"]["bot_group"])
        bot.save()
        self.external = UserFactory(username=overridden_zds_app["member"]["external_account"], password="anything")

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app["forum"]["beta_forum_id"],
            category=ForumCategoryFactory(position=1),
            position_in_category=1,
        )  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()
        self.tag = TagFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

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


@override_settings(ZDS_APP=overridden_zds_app)
class LastArticlesFeedRSSTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app["content"]["build_pdf_when_published"] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        overridden_zds_app["member"]["bot_account"] = self.mas.username

        bot = Group(name=overridden_zds_app["member"]["bot_group"])
        bot.save()
        self.external = UserFactory(username=overridden_zds_app["member"]["external_account"], password="anything")

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app["forum"]["beta_forum_id"],
            category=ForumCategoryFactory(position=1),
            position_in_category=1,
        )  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()
        self.tag = TagFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

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
