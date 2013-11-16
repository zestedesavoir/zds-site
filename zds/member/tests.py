# coding: utf-8

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from django_dynamic_fixture import G
from models import Profile


class SimpleTest(TestCase):
    def test_index(self):
        resp = self.client.get(reverse('zds.member.views.index'))
        self.assertEqual(resp.status_code, 200)

    def test_details(self):
        user = G(User, username='toto')
        profile = G(Profile, user=user)

        resp = self.client.get(reverse('zds.member.views.details',
                               args=[user.username]))
        self.assertEqual(resp.status_code, 200)

    def test_register(self):
        resp = self.client.get(reverse('zds.member.views.register_view'))
        self.assertEqual(resp.status_code, 200)

    def test_login(self):
        resp = self.client.get(reverse('zds.member.views.login_view'))
        self.assertEqual(resp.status_code, 200)

    def test_login_user(self):
        user = G(User, username='test')
        user.set_password('test')
        user.save()

        profile = G(Profile, user=user)

        resp = self.client.post(reverse('zds.member.views.login_view'),
                                {'username': 'test',
                                 'password': 'test'})

        self.assertEqual(self.client.session['_auth_user_id'], user.pk)

    def test_settings(self):
        user = G(User, username='test')
        user.set_password('test')
        user.save()

        profile = G(Profile, user=user)

        self.client.login(username='test', password='test')

        resp = self.client.get(reverse('zds.member.views.settings_profile'))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse('zds.member.views.settings_account'))
        self.assertEqual(resp.status_code, 200)
