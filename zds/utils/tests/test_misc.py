# coding: utf-8
from django.test import TestCase

from zds.utils.misc import contains_utf8mb4


class Misc(TestCase):
    def test_utf8mb4(self):
        self.assertFalse(contains_utf8mb4('abc'))
        self.assertFalse(contains_utf8mb4(u'abc'))
        self.assertFalse(contains_utf8mb4('abc€'))
        self.assertFalse(contains_utf8mb4(u'abc€'))
        self.assertTrue(contains_utf8mb4('a🐙tbc€'))
        self.assertTrue(contains_utf8mb4(u'a🐙tbc€'))
