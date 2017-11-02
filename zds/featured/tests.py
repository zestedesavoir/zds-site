# coding: utf-8
from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.featured.factories import FeaturedResourceFactory
from zds.featured.models import FeaturedResource, FeaturedMessage
from datetime import datetime, date


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


class FeaturedResourceCreateViewTest(TestCase):
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
