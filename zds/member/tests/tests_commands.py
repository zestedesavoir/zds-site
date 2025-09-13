import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from zds.member.tests.factories import ProfileFactory, UserFactory


class TestUnregisterCommand(TestCase):
    def setUp(self):
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")

    def test_unregister_command(self):
        def call_silent_command(arg: str):
            with open(os.devnull, "w") as f:
                call_command("unregister", "--force", arg, stdout=f, stderr=f)

        user = ProfileFactory()
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 1)

        call_silent_command("unexisting_user")
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 1)

        call_silent_command(user.user.username)
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 0)
        self.assertEqual(User.objects.filter().count(), 2)  # anonymous and external
