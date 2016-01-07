# coding: utf-8

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.member.factories import ProfileFactory, StaffProfileFactory


class PagesMemberTests(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory().user
        log = self.client.login(
            username=self.user1.username,
            password='hostel77')
        self.assertEqual(log, True)
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_subscribe_association(self):
        """To test the "subscription to the association" form."""

        long_str = u""
        for i in range(3100):
            long_str += u"A"

        result = self.client.post(
            reverse('pages-assoc-subscribe'),
            {
                'full_name': 'Anne Onyme',
                'email': 'anneonyme@test.com',
                'naissance': '01 janvier 1970',
                'adresse': '42 rue du savoir, appartement 42, 75000 Paris, France',
                'justification': long_str,
                'username': self.user1.username,
                'profile_url': settings.ZDS_APP['site']['url'] + reverse('member-detail',
                                                                         kwargs={'user_name': self.user1.username})
            },
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 0)

        result = self.client.post(
            reverse('pages-assoc-subscribe'),
            {
                'full_name': 'Anne Onyme',
                'email': 'anneonyme@test.com',
                'naissance': '01 janvier 1970',
                'adresse': '42 rue du savoir, appartement 42, 75000 Paris, France',
                'justification': 'Parce que l\'assoc est trop swag !',
                'username': self.user1.username,
                'profile_url': settings.ZDS_APP['site']['url'] + reverse('member-detail',
                                                                         kwargs={'user_name': self.user1.username})
            },
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 1)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)


class PagesStaffTests(TestCase):

    def setUp(self):
        self.staff = StaffProfileFactory().user
        log = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(log, True)

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)


class PagesGuestTests(TestCase):

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)

    def test_render_template(self):
        """Test: render_template() works and git_version is in template."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertTrue('git_version' in result.context[-1])
