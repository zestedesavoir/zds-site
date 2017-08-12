from django.conf import settings
from django.test import TestCase

from zds.utils.templatetags.remove_url_protocol import remove_url_protocol


class RemoveUrlProtocolTest(TestCase):

    def test_remove_protocole_when_local_url(self):
        self.assertEqual('/bla.html', remove_url_protocol('http://' + settings.ZDS_APP['site']['dns'] + '/bla.html'))
        self.assertEqual('/bla.html', remove_url_protocol('https://' + settings.ZDS_APP['site']['dns'] + '/bla.html'))

    def test_no_change_when_no_protocole(self):
        self.assertEqual('/bla.html', remove_url_protocol('/bla.html'))

    def test_no_change_when_extern_address(self):
        self.assertEqual('http://www.google.com/bla.html', remove_url_protocol('http://www.google.com/bla.html'))
