# coding: utf-8

from django.test import TestCase

from zds.utils.templatetags.quote_for_mp import quote_for_mp


class QuoteForMpTest(TestCase):

    def test_quote_for_mp(self):
        message = "Hi !\n I'm a test message !"
        success = "> Hi !\n > I'm a test message !"
        self.assertEqual(quote_for_mp(message), success)
