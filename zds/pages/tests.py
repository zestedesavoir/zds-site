# coding: utf-8

from django.test import TestCase

from django.core import mail
from django.core.urlresolvers import reverse

from zds import settings
from zds.member.factories import UserFactory, StaffFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.mp.models import PrivateTopic, PrivatePost
from zds.utils import slugify


class PagesMemberTests(TestCase):

    def setUp(self):
        self.user1 = UserFactory()
        log = self.client.login(
            username=self.user1.username,
            password='hostel77')
        self.assertEqual(log, True)

    def test_url_home(self):
        '''
        Test: check that home page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.home'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        '''
        Test: check that eula page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.eula'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        '''
        Test: check that about page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.about'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        '''
        Test: check that contact page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.contact'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        '''
        Test: check that association page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.association'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

class PagesStaffTests(TestCase):

    def setUp(self):
        self.staff = StaffFactory()
        log = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(log, True)

    def test_url_home(self):
        '''
        Test: check that home page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.home'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        '''
        Test: check that eula page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.eula'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        '''
        Test: check that about page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.about'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        '''
        Test: check that contact page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.contact'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        '''
        Test: check that association page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.association'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)


class PagesGuestTests(TestCase):

    def test_url_home(self):
        '''
        Test: check that home page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.home'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        '''
        Test: check that eula page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.eula'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        '''
        Test: check that about page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.about'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        '''
        Test: check that contact page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.contact'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        '''
        Test: check that association page is alive
        '''

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.pages.views.association'),
        )

        # Check username in new MP page
        self.assertEqual(result.status_code, 200)
