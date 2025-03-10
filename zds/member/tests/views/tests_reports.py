from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import PrivateTopic
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.utils.models import Alert


@override_for_contents()
class MemberTests(TutorialTestMixin, TestCase):
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

    def test_profile_report(self):
        profile = ProfileFactory()
        self.client.logout()
        alerts_count = Alert.objects.count()
        # test that authentication is required to report a profile
        result = self.client.post(reverse("report-profile", args=[profile.pk]), {"reason": "test"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(alerts_count, Alert.objects.count())
        # login and check it doesn't work without reason
        self.client.force_login(self.staff)
        result = self.client.post(reverse("report-profile", args=[profile.pk]), {"reason": ""}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(alerts_count, Alert.objects.count())
        # add a reason and check it works
        result = self.client.post(reverse("report-profile", args=[profile.pk]), {"reason": "test"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(alerts_count + 1, Alert.objects.count())
        # test alert solving
        alert = Alert.objects.latest("pubdate")
        pm_count = PrivateTopic.objects.count()
        result = self.client.post(reverse("solve-profile-alert", args=[alert.pk]), {"text": "ok"}, follow=False)
        self.assertEqual(result.status_code, 302)
        alert = Alert.objects.get(pk=alert.pk)  # refresh
        self.assertTrue(alert.solved)
        self.assertEqual(pm_count + 1, PrivateTopic.objects.count())
