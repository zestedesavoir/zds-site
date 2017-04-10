# coding: utf-8
import datetime
from django.test import TestCase

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory
from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Alert
from zds.utils.templatetags.interventions import alerts_list


class Misc(TestCase):
    def test_utf8mb4(self):
        self.assertFalse(contains_utf8mb4('abc'))
        self.assertFalse(contains_utf8mb4(u'abc'))
        self.assertFalse(contains_utf8mb4('abc€'))
        self.assertFalse(contains_utf8mb4(u'abc€'))
        self.assertTrue(contains_utf8mb4('a🐙tbc€'))
        self.assertTrue(contains_utf8mb4(u'a🐙tbc€'))

    def test_intervention_filter_for_tribunes(self):
        author = ProfileFactory()
        opinion = PublishedContentFactory(type='OPINION', author_list=[author.user])
        alerter = ProfileFactory()
        staff = StaffProfileFactory()
        alert = Alert()
        alert.scope = 'CONTENT'
        alert.author = alerter.user
        alert.content = opinion
        alert.pubdate = datetime.datetime.now()
        alert.text = 'Something to say.'
        alert.save()
        filter_result = alerts_list(staff.user)
        self.assertEqual(1, filter_result['nb_alerts'])
        self.assertEqual(alert.text, filter_result['alerts'][0]['text'])
