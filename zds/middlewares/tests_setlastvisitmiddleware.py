from datetime import datetime, timedelta

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.shortcuts import get_object_or_404

from zds.member.factories import ProfileFactory
from zds.member.models import Profile
from django.conf import settings
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['member']['update_last_visit_interval'] = 30


@override_settings(ZDS_APP=overridden_zds_app)
class SetLastVisitMiddlewareTest(TestCase):
    def setUp(self):
        self.user = ProfileFactory()

    def test_process_response(self):
        profile_pk = self.user.pk

        # login
        self.assertEqual(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'),
            True)

        # set last login to a recent date
        self.user.last_visit = datetime.now() - timedelta(seconds=10)
        self.user.save()

        # load a page
        self.client.get(reverse('homepage'))

        # the date of last visit should not have been updated
        profile = get_object_or_404(Profile, pk=profile_pk)
        self.assertTrue(datetime.now() - profile.last_visit > timedelta(seconds=5))

        # set last login to an old date
        self.user.last_visit = datetime.now() - timedelta(seconds=45)
        self.user.save()

        # load a page
        self.client.get(reverse('homepage'))

        # the date of last visit should have been updated
        profile = get_object_or_404(Profile, pk=profile_pk)
        self.assertTrue(datetime.now() - profile.last_visit < timedelta(seconds=5))
