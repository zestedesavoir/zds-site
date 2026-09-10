from django.conf import settings
from django.contrib.auth.models import Group

from zds.member.tests.factories import ProfileFactory, UserFactory


class TestWithBotsMixin:
    def create_bots(self):
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username
        self.anonymous = ProfileFactory(
            user=UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        ).user
        self.external = ProfileFactory(
            user=UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        ).user

        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()
        self.bot.user_set.add(self.mas.user)
        self.bot.user_set.add(self.anonymous)
        self.bot.user_set.add(self.external)
        self.bot.save()
