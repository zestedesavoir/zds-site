import collections
import datetime
from django.test import TestCase
from django.conf import settings
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory
from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Alert
from zds.utils.templatetags.interventions import alerts_list
from zds.utils.templatetags.remove_url_scheme import remove_url_scheme


class Misc(TestCase):
    def test_utf8mb4(self):
        self.assertFalse(contains_utf8mb4('abc'))
        self.assertFalse(contains_utf8mb4('abc'))
        self.assertFalse(contains_utf8mb4('abc€'))
        self.assertFalse(contains_utf8mb4('abc€'))
        self.assertTrue(contains_utf8mb4('a🐙tbc€'))
        self.assertTrue(contains_utf8mb4('a🐙tbc€'))

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

    def test_remove_url_scheme(self):
        Element = collections.namedtuple('element', ['name', 'given', 'expected'])
        oracle = {
            Element('cannonical http', 'http://{}/media/gallery/1/1.png'.format(settings.ZDS_APP['site']['dns']),
                    '/media/gallery/1/1.png'),
            Element('cannonical no scheme internal', '{}/media/gallery/1/1.png'.format(settings.ZDS_APP['site']['dns']),
                    '/media/gallery/1/1.png'),
            Element('cannonical no scheme external', 'example.com/media/gallery/1/1.png',
                    'example.com/media/gallery/1/1.png'),
            Element('cannonical https', 'https://{}/media/gallery/1/1.png'.format(settings.ZDS_APP['site']['dns']),
                    '/media/gallery/1/1.png'),
            Element('limit: empty url', '',
                    ''),
            Element('old bug: url in qstring', 'http://example.com?q=http://{}'.format(settings.ZDS_APP['site']['dns']),
                    'http://example.com?q=http://{}'.format(settings.ZDS_APP['site']['dns'])),
        }

        for element in oracle:
            # as we are not in py3 we do not have subTest method. so we use a bare for loop.
            self.assertEqual(remove_url_scheme(element.given), element.expected)
