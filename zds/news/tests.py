# coding: utf-8
from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.news.factories import NewsFactory
from zds.news.models import News


class NewsListViewTest(TestCase):
    def test_success_list_of_news(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('news-list'))

        self.assertEqual(200, response.status_code)

    def test_failure_list_of_news_with_unauthenticated_user(self):
        response = self.client.get(reverse('news-list'))

        self.assertEqual(302, response.status_code)

    def test_failure_list_of_news_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('news-list'))

        self.assertEqual(403, response.status_code)


class NewsCreateViewTest(TestCase):
    def test_success_create_news(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        self.assertEqual(0, News.objects.all().count())
        response = self.client.post(
            reverse('news-create'),
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
        self.assertEqual(1, News.objects.all().count())

    def test_failure_create_news_with_unauthenticated_user(self):
        response = self.client.get(reverse('news-create'))

        self.assertEqual(302, response.status_code)

    def test_failure_create_news_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('news-create'))

        self.assertEqual(403, response.status_code)


class NewsUpdateViewTest(TestCase):
    def test_success_update_news(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = NewsFactory()
        self.assertEqual(1, News.objects.all().count())
        response = self.client.post(
            reverse('news-update', args=[news.pk]),
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
        self.assertEqual(1, News.objects.all().count())

    def test_failure_create_news_with_unauthenticated_user(self):
        response = self.client.get(reverse('news-update', args=[42]))

        self.assertEqual(302, response.status_code)

    def test_failure_create_news_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('news-update', args=[42]))

        self.assertEqual(403, response.status_code)
