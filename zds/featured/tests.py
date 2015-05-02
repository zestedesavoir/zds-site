# coding: utf-8
from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.featured.factories import ResourceFeaturedFactory
from zds.featured.models import ResourceFeatured, MessageFeatured


class ResourceFeaturedListViewTest(TestCase):
    def test_success_list_of_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-list'))

        self.assertEqual(200, response.status_code)

    def test_failure_list_of_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-list'))

        self.assertEqual(302, response.status_code)

    def test_failure_list_of_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-list'))

        self.assertEqual(403, response.status_code)


class ResourceFeaturedCreateViewTest(TestCase):
    def test_success_create_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        self.assertEqual(0, ResourceFeatured.objects.all().count())
        response = self.client.post(
            reverse('featured-create'),
            {
                'title': 'title',
                'type': 'type',
                'image_url': 'image_url',
                'url': 'url',
                'authors': staff.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, ResourceFeatured.objects.all().count())

    def test_failure_create_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-create'))

        self.assertEqual(302, response.status_code)

    def test_failure_create_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-create'))

        self.assertEqual(403, response.status_code)


class ResourceFeaturedUpdateViewTest(TestCase):
    def test_success_update_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = ResourceFeaturedFactory()
        self.assertEqual(1, ResourceFeatured.objects.all().count())
        response = self.client.post(
            reverse('featured-update', args=[news.pk]),
            {
                'title': 'title',
                'type': 'type',
                'image_url': 'image_url',
                'url': 'url',
                'authors': staff.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, ResourceFeatured.objects.all().count())

    def test_failure_create_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-update', args=[42]))

        self.assertEqual(302, response.status_code)

    def test_failure_create_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-update', args=[42]))

        self.assertEqual(403, response.status_code)


class ResourceFeaturedDeleteViewTest(TestCase):
    def test_success_delete_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = ResourceFeaturedFactory()
        self.assertEqual(1, ResourceFeatured.objects.all().count())
        response = self.client.post(
            reverse('featured-delete', args=[news.pk]),
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, ResourceFeatured.objects.filter(pk=news.pk).count())

    def test_failure_delete_featured_with_unauthenticated_user(self):
        news = ResourceFeaturedFactory()
        response = self.client.get(reverse('featured-delete', args=[news.pk]))

        self.assertEqual(302, response.status_code)

    def test_failure_delete_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = ResourceFeaturedFactory()
        response = self.client.get(reverse('featured-delete', args=[news.pk]))

        self.assertEqual(403, response.status_code)


class ResourceFeaturedListDeleteViewTest(TestCase):
    def test_success_list_delete_featured(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = ResourceFeaturedFactory()
        news2 = ResourceFeaturedFactory()
        self.assertEqual(2, ResourceFeatured.objects.all().count())
        response = self.client.post(
            reverse('featured-list-delete'),
            {
                'items': [news.pk, news2.pk]
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, ResourceFeatured.objects.filter(pk=news.pk).count())
        self.assertEqual(0, ResourceFeatured.objects.filter(pk=news2.pk).count())

    def test_failure_list_delete_featured_with_unauthenticated_user(self):
        response = self.client.get(reverse('featured-list-delete'))

        self.assertEqual(302, response.status_code)

    def test_failure_list_delete_featured_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('featured-list-delete'))

        self.assertEqual(403, response.status_code)


class MessageFeaturedCreateUpdateViewTest(TestCase):
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
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageFeatured.objects.count())

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
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageFeatured.objects.count())

        response = self.client.post(
            reverse('featured-message-create'),
            {
                'message': 'message',
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageFeatured.objects.count())
