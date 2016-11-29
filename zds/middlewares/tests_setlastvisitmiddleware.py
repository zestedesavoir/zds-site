# coding: utf-8

from datetime import datetime, timedelta

from django.test import TestCase
from django.core.urlresolvers import reverse
from zds import settings
from django.test.utils import override_settings

from zds.member.factories import ProfileFactory


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['member']['update_last_visit_interval'] = 30


@override_settings(ZDS_APP=overrided_zds_app)
class SetLastVisitMiddlewareTest(TestCase):
    def setUp(self):
        self.user = ProfileFactory()

    def test_process_response(self):
        # set last login
        self.user.last_login = datetime.now() - timedelta(seconds=10)

        # login
        self.assertEqual(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'),
            True)

        # load a page
        self.client.get(reverse('homepage'))

        # the date of last visit should not have been updated
        self.assertTrue(datetime.now() - self.user.last_login > timedelta(seconds=5))
