from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.member.models import TokenForgotPassword
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory


class MemberTests(TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        self.category1 = ForumCategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.staff = StaffProfileFactory().user

        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_forgot_password(self):
        """To test nominal scenario of a lost password."""

        # Empty the test outbox
        mail.outbox = []

        result = self.client.post(
            reverse("member-forgot-password"),
            {
                "username": self.mas.user.username,
                "email": "",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEqual(len(mail.outbox), 1)

        # clic on the link which has been sent in mail
        user = User.objects.get(username=self.mas.user.username)

        token = TokenForgotPassword.objects.get(user=user)
        result = self.client.get(settings.ZDS_APP["site"]["url"] + token.get_absolute_url(), follow=False)

        self.assertEqual(result.status_code, 200)
