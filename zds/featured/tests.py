import os
import shutil
from copy import deepcopy
from datetime import datetime, date
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.featured.factories import FeaturedResourceFactory
from zds.featured.models import FeaturedResource, FeaturedMessage, FeaturedRequested
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory
from zds.gallery.factories import GalleryFactory, ImageFactory
from zds.tutorialv2.factories import PublishedContentFactory


overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


stringof2001chars = 'http://url.com/'
for i in range(198):
    stringof2001chars += '0123456789'
stringof2001chars += '12.jpg'


class FeaturedResourceListViewTest(TestCase):
    def test_success_list_of_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-list'))

        self.assertEqual(200, response.status_code)

    def test_failure_list_of_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-resource-list'))

        self.assertEqual(403, response.status_code)

    def test_failure_list_of_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-list'))

        self.assertEqual(403, response.status_code)


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class FeaturedResourceCreateViewTest(TestCase):
    def setUp(self):
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

    def test_success_create_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )

        self.assertTrue(login_check)
        self.assertEqual(0, FeaturedResource.objects.all().count())

        pubdate = date(2016, 1, 1).strftime('%d/%m/%Y %H:%M:%S')

        fields = {
            'title': 'title',
            'type': 'type',
            'image_url': 'http://test.com/image.png',
            'url': 'http://test.com',
            'authors': staff.user.username,
            'pubdate': pubdate
        }

        response = self.client.post(reverse('featured-resource-create'), fields, follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FeaturedResource.objects.all().count())

        featured = FeaturedResource.objects.first()

        for field, value in list(fields.items()):
            if field != 'pubdate':
                self.assertEqual(value, getattr(featured, field), msg='Error on {}'.format(field))
            else:
                self.assertEqual(value, featured.pubdate.strftime('%d/%m/%Y %H:%M:%S'))

        # now with major_update
        fields['major_update'] = 'on'

        response = self.client.post(reverse('featured-resource-create'), fields, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, FeaturedResource.objects.all().count())

        featured = FeaturedResource.objects.last()
        self.assertTrue((datetime.now() - featured.pubdate).total_seconds() < 10)

    def test_failure_create_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-resource-create'))

        self.assertEqual(403, response.status_code)

    def test_failure_create_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-create'))

        self.assertEqual(403, response.status_code)

    def test_failure_too_long_url(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        self.assertEqual(0, FeaturedResource.objects.all().count())
        response = self.client.post(
            reverse('featured-resource-create'),
            {
                'title': 'title',
                'type': 'type',
                'image_url': stringof2001chars,
                'url': 'http://test.com',
                'authors': staff.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, FeaturedResource.objects.all().count())

        response = self.client.post(
            reverse('featured-resource-create'),
            {
                'title': 'title',
                'type': 'type',
                'image_url': 'http://test.com/image.png',
                'url': stringof2001chars,
                'authors': staff.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, FeaturedResource.objects.all().count())

    def test_success_initial_content(self):
        author = ProfileFactory().user
        author2 = ProfileFactory().user
        tutorial = PublishedContentFactory(author_list=[author, author2])
        gallery = GalleryFactory()
        image = ImageFactory(gallery=gallery)
        tutorial.image = image
        tutorial.save()
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)
        response = self.client.get('{}{}'.format(reverse('featured-resource-create'),
                                                 '?content_type=published_content&content_id={}'.format(tutorial.pk)))
        initial_dict = response.context['form'].initial
        self.assertEqual(initial_dict['title'], tutorial.title)
        self.assertEqual(initial_dict['authors'], '{}, {}'.format(author, author2))
        self.assertEqual(initial_dict['type'], _('Un tutoriel'))
        self.assertEqual(initial_dict['url'], 'http://testserver{}'.format(tutorial.get_absolute_url_online()))
        self.assertEqual(initial_dict['image_url'], image.physical.url)

    def test_success_initial_content_topic(self):
        author = ProfileFactory().user
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=author)
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertTrue(login_check)
        response = self.client.get('{}?content_type=topic&content_id={}'
                                   .format(reverse('featured-resource-create'), topic.id))
        initial_dict = response.context['form'].initial
        self.assertEqual(initial_dict['title'], topic.title)
        self.assertEqual(initial_dict['authors'], str(author))
        self.assertEqual(initial_dict['type'], _('Un sujet'))
        self.assertEqual(initial_dict['url'], 'http://testserver{}'.format(topic.get_absolute_url()))

    def test_failure_initial_content_not_found(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get('{}?content_type=published_content&content_id=42'
                                   .format(reverse('featured-resource-create')))
        self.assertContains(response, _('Le contenu est introuvable'))

    def tearDown(self):
        if os.path.isdir(overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


class FeaturedResourceUpdateViewTest(TestCase):
    def test_success_update_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = FeaturedResourceFactory()
        self.assertEqual(1, FeaturedResource.objects.all().count())

        old_featured = FeaturedResource.objects.first()

        pubdate = date(2016, 1, 1).strftime('%d/%m/%Y %H:%M:%S')

        fields = {
            'title': 'title',
            'type': 'type',
            'image_url': 'http://test.com/image.png',
            'url': 'http://test.com',
            'authors': staff.user.username,
            'pubdate': pubdate
        }

        response = self.client.post(reverse('featured-resource-update', args=[news.pk]), fields, follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FeaturedResource.objects.all().count())

        featured = FeaturedResource.objects.first()

        for field, value in list(fields.items()):
            self.assertNotEqual(getattr(featured, field), getattr(old_featured, field))

            if field != 'pubdate':
                self.assertEqual(value, getattr(featured, field), msg='Error on {}'.format(field))
            else:
                self.assertEqual(value, featured.pubdate.strftime('%d/%m/%Y %H:%M:%S'))

        # now with major_update
        self.assertFalse((datetime.now() - featured.pubdate).total_seconds() < 10)

        fields['major_update'] = 'on'

        response = self.client.post(reverse('featured-resource-update', args=[news.pk]), fields, follow=True)
        self.assertEqual(200, response.status_code)
        featured = FeaturedResource.objects.first()
        self.assertTrue((datetime.now() - featured.pubdate).total_seconds() < 10)

    def test_failure_create_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-resource-update', args=[42]))

        self.assertEqual(403, response.status_code)

    def test_failure_create_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-update', args=[42]))

        self.assertEqual(403, response.status_code)


class FeaturedResourceDeleteViewTest(TestCase):
    def test_success_delete_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = FeaturedResourceFactory()
        self.assertEqual(1, FeaturedResource.objects.all().count())
        response = self.client.post(
            reverse('featured-resource-delete', args=[news.pk]),
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, FeaturedResource.objects.filter(pk=news.pk).count())

    def test_failure_delete_featured_with_unauthenticated_user(self):
        news = FeaturedResourceFactory()
        response = self.client.get(reverse('featured-resource-delete', args=[news.pk]))

        self.assertEqual(403, response.status_code)

    def test_failure_delete_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = FeaturedResourceFactory()
        response = self.client.get(reverse('featured-resource-delete', args=[news.pk]))

        self.assertEqual(403, response.status_code)


class FeaturedResourceListDeleteViewTest(TestCase):
    def test_success_list_delete_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = FeaturedResourceFactory()
        news2 = FeaturedResourceFactory()
        self.assertEqual(2, FeaturedResource.objects.all().count())
        response = self.client.post(
            reverse('featured-resource-list-delete'),
            {
                'items': [news.pk, news2.pk]
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, FeaturedResource.objects.filter(pk=news.pk).count())
        self.assertEqual(0, FeaturedResource.objects.filter(pk=news2.pk).count())

    def test_failure_list_delete_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-resource-list-delete'))

        self.assertEqual(403, response.status_code)

    def test_failure_list_delete_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-list-delete'))

        self.assertEqual(403, response.status_code)


class FeaturedMessageCreateUpdateViewTest(TestCase):
    def test_success_list_create_message(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('featured-message-create'),
            {
                'message': 'message',
                'url': 'http://test.com',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FeaturedMessage.objects.count())

    def test_create_only_one_message_in_system(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('featured-message-create'),
            {
                'message': 'message',
                'url': 'http://test.com',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FeaturedMessage.objects.count())

        response = self.client.post(
            reverse('featured-message-create'),
            {
                'message': 'message',
                'url': 'http://test.com',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FeaturedMessage.objects.count())


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class FeaturedRequestListViewTest(TestCase):
    def setUp(self):
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

    def test_success_list(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-requests'))

        self.assertEqual(200, response.status_code)

    def test_failure_list_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-resource-requests'))

        self.assertEqual(403, response.status_code)

    def test_failure_list_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-requests'))

        self.assertEqual(403, response.status_code)

    def test_filters(self):
        # create topic and content and toggle request
        author = ProfileFactory().user
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=author)

        FeaturedRequested.objects.toogle_request(topic, author)

        tutorial = PublishedContentFactory(author_list=[author])
        gallery = GalleryFactory()
        image = ImageFactory(gallery=gallery)
        tutorial.image = image
        tutorial.save()

        FeaturedRequested.objects.toogle_request(tutorial, author)

        # without filter
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-resource-requests'))
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['featured_request_list']), 2)
        self.assertTrue(any(r.content_object == topic for r in response.context['featured_request_list']))
        self.assertTrue(any(r.content_object == tutorial for r in response.context['featured_request_list']))

        # filter topic
        response = self.client.get(reverse('featured-resource-requests') + '?type=topic')
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['featured_request_list']), 1)
        self.assertTrue(any(r.content_object == topic for r in response.context['featured_request_list']))
        self.assertFalse(any(r.content_object == tutorial for r in response.context['featured_request_list']))

        # filter tuto
        response = self.client.get(reverse('featured-resource-requests') + '?type=content')
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['featured_request_list']), 1)
        self.assertFalse(any(r.content_object == topic for r in response.context['featured_request_list']))
        self.assertTrue(any(r.content_object == tutorial for r in response.context['featured_request_list']))

        # reject topic
        content_type = ContentType.objects.get_for_model(topic)
        q = FeaturedRequested.objects.get(object_id=topic.pk, content_type__pk=content_type.pk)
        q.rejected = True
        q.save()

        response = self.client.get(reverse('featured-resource-requests') + '?type=topic')
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['featured_request_list']), 0)

        # filter ignored
        response = self.client.get(reverse('featured-resource-requests') + '?type=ignored')
        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.context['featured_request_list']), 1)
        self.assertTrue(any(r.content_object == topic for r in response.context['featured_request_list']))

    def tearDown(self):
        if os.path.isdir(overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


class FeaturedRequestUpdateViewTest(TestCase):

    def test_update(self):
        # create topic and content and toggle request
        author = ProfileFactory().user
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=author)

        FeaturedRequested.objects.toogle_request(topic, author)

        # ignore
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        content_type = ContentType.objects.get_for_model(topic)
        q = FeaturedRequested.objects.get(object_id=topic.pk, content_type__pk=content_type.pk)
        self.assertFalse(q.rejected)

        response = self.client.post(
            reverse('featured-resource-request-update', kwargs={'pk': q.pk}),
            {
                'operation': 'REJECT'
            },
            follow=False
        )
        self.assertEqual(200, response.status_code)

        q = FeaturedRequested.objects.get(pk=q.pk)
        self.assertTrue(q.rejected)

        response = self.client.post(
            reverse('featured-resource-request-update', kwargs={'pk': q.pk}),
            {
                'operation': 'CONSIDER'
            },
            follow=False
        )
        self.assertEqual(200, response.status_code)

        q = FeaturedRequested.objects.get(pk=q.pk)
        self.assertFalse(q.rejected)


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class FeaturedRequestToggleTest(TestCase):
    def setUp(self):
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

    def test_toggle(self):
        author = ProfileFactory()
        login_check = self.client.login(
            username=author.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        # create topic and toggle request
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=author.user)

        response = self.client.post(
            reverse('topic-edit') + '?topic={}'.format(topic.pk),
            {
                'request_featured': 1
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(FeaturedRequested.objects.count(), 1)
        r = FeaturedRequested.objects.last()
        self.assertEqual(r.content_object, topic)
        self.assertIn(author.user, r.users_voted.all())

        # create tutorial and toggle request
        tutorial = PublishedContentFactory(author_list=[author.user])
        gallery = GalleryFactory()
        image = ImageFactory(gallery=gallery)
        tutorial.image = image
        tutorial.save()

        response = self.client.post(
            reverse('content:request-featured', kwargs={'pk': tutorial.pk}),
            {
                'request_featured': 1
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(FeaturedRequested.objects.count(), 2)
        r = FeaturedRequested.objects.last()
        self.assertEqual(r.content_object, tutorial)
        self.assertIn(author.user, r.users_voted.all())

        # create opinion: cannot toggle request!
        opinion = PublishedContentFactory(type='OPINION', author_list=[author.user])
        gallery = GalleryFactory()
        image = ImageFactory(gallery=gallery)
        opinion.image = image
        opinion.save()

        response = self.client.post(
            reverse('content:request-featured', kwargs={'pk': opinion.pk}),
            {
                'request_featured': 1
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(403, response.status_code)
        self.assertEqual(FeaturedRequested.objects.count(), 2)

        # set tutorial as obsolete: cannot toggle
        tutorial.is_obsolete = True
        tutorial.save()

        response = self.client.post(
            reverse('content:request-featured', kwargs={'pk': tutorial.pk}),
            {
                'request_featured': 1
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(403, response.status_code)

        r = FeaturedRequested.objects.get(pk=r.pk)
        self.assertEqual(r.content_object, tutorial)
        self.assertIn(author.user, r.users_voted.all())

    def tearDown(self):
        if os.path.isdir(overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
