import os
import shutil
from copy import deepcopy
from datetime import datetime, date
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.featured.factories import FeaturedResourceFactory
from zds.featured.models import FeaturedResource, FeaturedMessage
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

        self.assertEqual(302, response.status_code)

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

        self.assertEqual(302, response.status_code)

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
                                                 '?content_type=published_content&content_id=1'))
        initial_dict = response.context['form'].initial
        self.assertEqual(initial_dict['title'], tutorial.title)
        self.assertEqual(initial_dict['authors'], '{}, {}'.format(author, author2))
        self.assertEqual(initial_dict['type'], _('Un tutoriel'))
        self.assertEqual(initial_dict['url'], 'http://testserver/tutoriels/1/mon-contenu-no0/')
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

        self.assertEqual(302, response.status_code)

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

        self.assertEqual(302, response.status_code)

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

        self.assertEqual(302, response.status_code)

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
