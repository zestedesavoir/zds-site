import os

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import Group

from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.forum.factories import ForumFactory, CategoryFactory
from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM, LastArticlesFeedRSS, LastArticlesFeedATOM
from zds.tutorialv2.factories import LicenceFactory, SubCategoryFactory, PublishableContentFactory, ContainerFactory, \
    ExtractFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
class LastTutorialsFeedRSSTest(TestCase, TutorialTestMixin):

    def setUp(self):
        settings.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        overridden_zds_app['member']['bot_account'] = self.mas.username

        bot = Group(name=overridden_zds_app['member']['bot_group'])
        bot.save()
        self.external = UserFactory(
            username=overridden_zds_app['member']['external_account'],
            password='anything')

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode='W')
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
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
        """ Test that base parameters are Ok """

        self.assertEqual(self.tutofeed.link, '/tutoriels/')
        reftitle = 'Tutoriels sur {}'.format(overridden_zds_app['site']['literal_name'])
        self.assertEqual(self.tutofeed.title, reftitle)
        refdescription = 'Les derniers tutoriels parus sur {}.'.format(overridden_zds_app['site']['literal_name'])
        self.assertEqual(self.tutofeed.description, refdescription)

        atom = LastTutorialsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """ basic test sending back the tutorial """

        ret = list(self.tutofeed.items())
        self.assertEqual(ret[0].content, self.tuto)

    def test_get_pubdate(self):
        """ test the return value of pubdate """

        ref = PublishedContent.objects.get(content__pk=self.tuto.pk).publication_date
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_pubdate(item=tuto)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """ test the return value of title """

        ref = self.tuto.title
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_title(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """ test the return value of description """

        ref = self.tuto.description
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_description(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """ test the return value of author name """

        ref = self.user_author.username
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_author_name(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """ test the return value of item link """

        ref = self.tuto.get_absolute_url_online()
        tuto = list(self.tutofeed.items())[0]
        ret = self.tutofeed.item_link(item=tuto)
        self.assertEqual(ret, ref)


@override_settings(ZDS_APP=overridden_zds_app)
class LastArticlesFeedRSSTest(TestCase, TutorialTestMixin):

    def setUp(self):
        settings.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        overridden_zds_app['member']['bot_account'] = self.mas.username

        bot = Group(name=overridden_zds_app['member']['bot_group'])
        bot.save()
        self.external = UserFactory(
            username=overridden_zds_app['member']['external_account'],
            password='anything')

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        # create an article
        self.article = PublishableContentFactory(type='ARTICLE')
        self.article.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.article.gallery, user=self.user_author, mode='W')
        self.article.licence = self.licence
        self.article.subcategory.add(self.subcategory)
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
        """ Test that base parameters are Ok """

        self.assertEqual(self.articlefeed.link, '/articles/')
        reftitle = 'Articles sur {}'.format(overridden_zds_app['site']['literal_name'])
        self.assertEqual(self.articlefeed.title, reftitle)
        refdescription = 'Les derniers articles parus sur {}.'.format(overridden_zds_app['site']['literal_name'])
        self.assertEqual(self.articlefeed.description, refdescription)

        atom = LastArticlesFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """ basic test sending back the article """

        ret = list(self.articlefeed.items())
        self.assertEqual(ret[0].content, self.article)

    def test_get_pubdate(self):
        """ test the return value of pubdate """

        ref = PublishedContent.objects.get(content__pk=self.article.pk).publication_date
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_pubdate(item=article)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """ test the return value of title """

        ref = self.article.title
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_title(item=article)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """ test the return value of description """

        ref = self.article.description
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_description(item=article)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """ test the return value of author name """

        ref = self.user_author.username
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_author_name(item=article)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """ test the return value of item link """

        ref = self.article.get_absolute_url_online()
        article = list(self.articlefeed.items())[0]
        ret = self.articlefeed.item_link(item=article)
        self.assertEqual(ret, ref)
