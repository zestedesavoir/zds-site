# coding: utf-8

from django.test import TestCase
from django.test.client import Client


class PagesTests(TestCase):
    def test_url_home(self):
        '''Tests viewing home page'''
        client = Client()
        self.assertEqual(200, client.get('/').status_code)
