from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.member.models import BannedEmailProvider, NewEmailProvider, TokenRegister
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory


class EmailProvidersTests(TestCase):
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

    def test_new_provider_with_email_edit(self):
        new_providers_count = NewEmailProvider.objects.count()
        user = ProfileFactory().user
        self.client.force_login(user)
        # Edit the email with an unknown provider
        self.client.post(
            reverse("update-username-email-member"),
            {"username": user.username, "email": "test@unknown-provider-edit.com", "password": "hostel77"},
            follow=False,
        )
        # A new provider object should have been created
        self.assertEqual(new_providers_count + 1, NewEmailProvider.objects.count())

    def test_new_providers_list(self):
        # create a new provider
        user = ProfileFactory().user
        provider = NewEmailProvider.objects.create(use="NEW_ACCOUNT", user=user, provider="test.com")
        # check that the list is not available for a non-staff member
        self.client.logout()
        result = self.client.get(reverse("new-email-providers"), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.force_login(user)
        result = self.client.get(reverse("new-email-providers"), follow=False)
        self.assertEqual(result.status_code, 403)
        # and that it contains the provider we created
        self.client.force_login(self.staff)
        result = self.client.get(reverse("new-email-providers"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertIn(provider, result.context["providers"])

    def test_check_new_provider(self):
        # create two new providers
        user = ProfileFactory().user
        provider1 = NewEmailProvider.objects.create(use="NEW_ACCOUNT", user=user, provider="test1.com")
        provider2 = NewEmailProvider.objects.create(use="EMAIl_EDIT", user=user, provider="test2.com")
        # check that this option is only available for a staff member
        self.client.force_login(user)
        result = self.client.post(reverse("check-new-email-provider", args=[provider1.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        # test approval
        self.client.force_login(self.staff)
        result = self.client.post(reverse("check-new-email-provider", args=[provider1.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(NewEmailProvider.objects.filter(pk=provider1.pk).exists())
        self.assertFalse(BannedEmailProvider.objects.filter(provider=provider1.provider).exists())
        # test ban
        self.client.force_login(self.staff)
        result = self.client.post(reverse("check-new-email-provider", args=[provider2.pk]), {"ban": "on"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(NewEmailProvider.objects.filter(pk=provider2.pk).exists())
        self.assertTrue(BannedEmailProvider.objects.filter(provider=provider2.provider).exists())

    def test_banned_providers_list(self):
        user = ProfileFactory().user
        # create a banned provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider="test.com")
        # check that the list is not available for a non-staff member
        self.client.logout()
        result = self.client.get(reverse("banned-email-providers"), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.force_login(user)
        result = self.client.get(reverse("banned-email-providers"), follow=False)
        self.assertEqual(result.status_code, 403)
        # and that it contains the provider we created
        self.client.force_login(self.staff)
        result = self.client.get(reverse("banned-email-providers"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertIn(provider, result.context["providers"])

    def test_add_banned_provider(self):
        # test that this page is only available for staff
        user = ProfileFactory().user
        self.client.logout()
        result = self.client.get(reverse("add-banned-email-provider"), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.force_login(user)
        result = self.client.get(reverse("add-banned-email-provider"), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.force_login(self.staff)
        result = self.client.get(reverse("add-banned-email-provider"), follow=False)
        self.assertEqual(result.status_code, 200)

        # add a provider
        result = self.client.post(reverse("add-banned-email-provider"), {"provider": "new-provider.com"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertTrue(BannedEmailProvider.objects.filter(provider="new-provider.com").exists())

        # check that it cannot be added again
        result = self.client.post(reverse("add-banned-email-provider"), {"provider": "new-provider.com"}, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(1, BannedEmailProvider.objects.filter(provider="new-provider.com").count())

    def test_members_with_provider(self):
        # create two members with the same provider
        member1 = ProfileFactory().user
        member2 = ProfileFactory().user
        member1.email = "test1@test-members.com"
        member1.save()
        member2.email = "test2@test-members.com"
        member2.save()
        # ban this provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider="test-members.com")
        # check that this page is only available for staff
        self.client.logout()
        result = self.client.get(reverse("members-with-provider", args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.force_login(member1)
        result = self.client.get(reverse("members-with-provider", args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.force_login(self.staff)
        result = self.client.get(reverse("members-with-provider", args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 200)
        # check that it contains the two members
        self.assertIn(member1.profile, result.context["members"])
        self.assertIn(member2.profile, result.context["members"])

    def test_remove_banned_provider(self):
        user = ProfileFactory().user
        # add a banned provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider="test-remove.com")
        # check that this option is only available for a staff member
        self.client.force_login(user)
        result = self.client.post(reverse("check-new-email-provider", args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        # test that it removes the provider
        self.client.force_login(self.staff)
        result = self.client.post(reverse("remove-banned-email-provider", args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(BannedEmailProvider.objects.filter(pk=provider.pk).exists())
