# coding: utf-8
from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.news.factories import NewsFactory
from zds.news.models import News, MessageNews


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


class NewsDeleteViewTest(TestCase):
    def test_success_delete_news(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = NewsFactory()
        self.assertEqual(1, News.objects.all().count())
        response = self.client.post(
            reverse('news-delete', args=[news.pk]),
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, News.objects.filter(pk=news.pk).count())

    def test_failure_delete_news_with_unauthenticated_user(self):
        news = NewsFactory()
        response = self.client.get(reverse('news-delete', args=[news.pk]))

        self.assertEqual(302, response.status_code)

    def test_failure_delete_news_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = NewsFactory()
        response = self.client.get(reverse('news-delete', args=[news.pk]))

        self.assertEqual(403, response.status_code)


class NewsListDeleteViewTest(TestCase):
    def test_success_list_delete_news(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        news = NewsFactory()
        news2 = NewsFactory()
        self.assertEqual(2, News.objects.all().count())
        response = self.client.post(
            reverse('news-list-delete'),
            {
                'items': [news.pk, news2.pk]
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, News.objects.filter(pk=news.pk).count())
        self.assertEqual(0, News.objects.filter(pk=news2.pk).count())

    def test_failure_list_delete_news_with_unauthenticated_user(self):
        response = self.client.get(reverse('news-list-delete'))

        self.assertEqual(302, response.status_code)

    def test_failure_list_delete_news_with_user_not_staff(self):
        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('news-list-delete'))

        self.assertEqual(403, response.status_code)


class MessageNewsCreateUpdateViewTest(TestCase):
    def test_success_list_create_message(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('news-message-create'),
            {
                'message': 'message',
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageNews.objects.count())

    def test_create_only_one_message_in_system(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('news-message-create'),
            {
                'message': 'message',
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageNews.objects.count())

        response = self.client.post(
            reverse('news-message-create'),
            {
                'message': 'message',
                'url': 'url',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MessageNews.objects.count())
