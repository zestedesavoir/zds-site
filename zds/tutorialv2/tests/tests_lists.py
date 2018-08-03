from django.contrib.auth.models import Group

import os
import datetime
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, \
    SubCategoryFactory, PublishedContentFactory, ValidationFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from zds.gallery.factories import UserGalleryFactory
from zds.forum.factories import ForumFactory, CategoryFactory
from zds.utils.factories import CategoryFactory as ContentCategoryFactory
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class ContentTests(TestCase, TutorialTestMixin):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        overridden_zds_app['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode='W')
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        bot = Group(name=overridden_zds_app['member']['bot_group'])
        bot.save()
        self.external = UserFactory(
            username=overridden_zds_app['member']['external_account'],
            password='anything')

    def test_public_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type='ARTICLE')
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type='ARTICLE')
        self.client.logout()
        resp = self.client.get(reverse('publication:list') + '?type=tutorial')
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse('publication:list') + '?type=article')
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]) + '?filter=public')
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]) + '?filter=redaction')
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=public')
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=redaction')
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=chuck-norris')
        self.assertEqual(resp.status_code, 404)

    def _create_and_publish_type_in_subcategory(self, content_type, subcategory):
        tuto_1 = PublishableContentFactory(type=content_type, author_list=[self.user_author])
        tuto_1.subcategory.add(subcategory)
        tuto_1.save()
        tuto_1_draft = tuto_1.load_version()
        publish_content(tuto_1, tuto_1_draft, is_major_update=True)

    def test_list_categories(self):
        category_1 = ContentCategoryFactory()
        subcategory_1 = SubCategoryFactory(category=category_1)
        subcategory_2 = SubCategoryFactory(category=category_1)
        # Not in context if nothing published inside this subcategory
        SubCategoryFactory(category=category_1)

        for _ in range(5):
            self._create_and_publish_type_in_subcategory('TUTORIAL', subcategory_1)
            self._create_and_publish_type_in_subcategory('ARTICLE', subcategory_2)

        self.client.logout()
        resp = self.client.get(reverse('publication:list'))

        context_categories = list(resp.context_data['categories'])
        self.assertEqual(context_categories[0].contents_count, 10)
        self.assertEqual(context_categories[0].subcategories, [subcategory_1, subcategory_2])
        self.assertEqual(context_categories, [category_1])

    def test_private_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type='ARTICLE')
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type='ARTICLE')
        self.client.login(
            username=self.user_author.username,
            password='hostel77')
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]))
        self.assertContains(resp, tutorial.title)
        self.assertContains(resp, tutorial_unpublished.title)
        self.assertContains(resp, 'content-illu')
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]))
        self.assertContains(resp, article.title)
        self.assertContains(resp, article_unpublished.title)
        self.assertContains(resp, 'content-illu')

    def test_validation_list(self):
        """ensure the behavior of the `validation:list` page (with filters)"""

        text = 'Ceci est un éléphant'

        tuto_not_reserved = PublishableContentFactory(type='TUTORIAL', author_list=[self.user_author])
        tuto_reserved = PublishableContentFactory(type='TUTORIAL', author_list=[self.user_author])
        article_not_reserved = PublishableContentFactory(type='ARTICLE', author_list=[self.user_author])
        article_reserved = PublishableContentFactory(type='ARTICLE', author_list=[self.user_author])

        all_contents = [tuto_not_reserved, tuto_reserved, article_not_reserved, article_reserved]
        reserved_contents = [tuto_reserved, article_reserved]

        # apply a filter to test category filter
        subcat = SubCategoryFactory()
        article_reserved.subcategory.add(subcat)
        article_reserved.save()

        # send in validation
        for content in all_contents:
            v = ValidationFactory(content=content, status='PENDING')
            v.date_proposition = datetime.datetime.now()
            v.version = content.sha_draft
            v.comment_authors = text

            if content in reserved_contents:
                v.validator = self.user_staff
                v.date_reserve = datetime.datetime.now()
                v.status = 'PENDING_V'

            v.save()

        # first, test access for public
        result = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(result.status_code, 302)  # get 302 → redirection to login

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(result.status_code, 403)  # get 403 not allowed

        self.client.logout()

        # connect with staff:
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        response = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(response.status_code, 200)  # OK

        validations = response.context['validations']
        self.assertEqual(len(validations), 4)  # a total of 4 contents in validation

        # test filters
        response = self.client.get(reverse('validation:list') + '?type=article', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse('validation:list') + '?type=tuto', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse('validation:list') + '?type=orphan', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 not-reserved content

        for validation in validations:
            self.assertFalse(validation.content in reserved_contents)

        response = self.client.get(reverse('validation:list') + '?type=reserved', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 reserved content

        for validation in validations:
            self.assertTrue(validation.content in reserved_contents)

        response = self.client.get(reverse('validation:list') + '?subcategory={}'.format(subcat.pk), follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 1)  # 1 content with this category

        self.assertEqual(validations[0].content, article_reserved)  # the right content
