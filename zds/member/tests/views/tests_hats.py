from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.pages.models import GroupContact
from zds.utils.models import Hat, HatRequest


class HatTests(TestCase):
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

    def test_hats_on_profile(self):
        hat_name = "A hat"

        profile = ProfileFactory()
        user = profile.user
        # Test that hats don't appear if there are no hats
        self.client.force_login(user)
        result = self.client.get(profile.get_absolute_url())
        self.assertNotContains(result, _("Casquettes"))
        # Test that they don't appear with a staff member but that the link to add one does appear
        self.client.force_login(self.staff)
        result = self.client.get(profile.get_absolute_url())
        self.assertNotContains(result, _("Casquettes"))
        self.assertContains(result, _("Ajouter une casquette"))
        # Add a hat and check that it appears
        self.client.post(reverse("add-hat", args=[user.pk]), {"hat": hat_name}, follow=False)
        self.assertIn(hat_name, profile.hats.values_list("name", flat=True))
        result = self.client.get(profile.get_absolute_url())
        self.assertContains(result, _("Casquettes"))
        self.assertContains(result, hat_name)
        # And also for a member that is not staff
        self.client.force_login(user)
        result = self.client.get(profile.get_absolute_url())
        self.assertContains(result, _("Casquettes"))
        self.assertContains(result, hat_name)
        # Test that a hat linked to a group appears
        result = self.client.get(self.staff.profile.get_absolute_url())
        self.assertContains(result, _("Casquettes"))
        self.assertContains(result, "Staff")

    def test_add_hat(self):
        short_hat = "A new hat"
        long_hat = "A very long hat" * 3
        utf8mb4_hat = "🍊"

        profile = ProfileFactory()
        user = profile.user
        # check that this option is only available for a staff member
        self.client.force_login(user)
        result = self.client.post(reverse("add-hat", args=[user.pk]), {"hat": short_hat}, follow=False)
        self.assertEqual(result.status_code, 403)
        # login as staff
        self.client.force_login(self.staff)
        # test that it doesn't work with a too long hat (> 40 characters)
        result = self.client.post(reverse("add-hat", args=[user.pk]), {"hat": long_hat}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(long_hat, profile.hats.values_list("name", flat=True))
        # test that it doesn't work with a hat using utf8mb4 characters
        result = self.client.post(reverse("add-hat", args=[user.pk]), {"hat": utf8mb4_hat}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(utf8mb4_hat, profile.hats.values_list("name", flat=True))
        # test that it doesn't work with a hat linked to a group
        result = self.client.post(reverse("add-hat", args=[user.pk]), {"hat": "Staff"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(long_hat, profile.hats.values_list("name", flat=True))
        # test that it works with a short hat (<= 40 characters)
        result = self.client.post(reverse("add-hat", args=[user.pk]), {"hat": short_hat}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertIn(short_hat, profile.hats.values_list("name", flat=True))
        # test that if the hat already exists, it is used
        result = self.client.post(reverse("add-hat", args=[self.staff.pk]), {"hat": short_hat}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertIn(short_hat, self.staff.profile.hats.values_list("name", flat=True))
        self.assertEqual(Hat.objects.filter(name=short_hat).count(), 1)

    def test_remove_hat(self):
        hat_name = "A hat"

        profile = ProfileFactory()
        user = profile.user
        # add a hat with a staff member
        self.client.force_login(self.staff)
        self.client.post(reverse("add-hat", args=[user.pk]), {"hat": hat_name}, follow=False)
        self.assertIn(hat_name, profile.hats.values_list("name", flat=True))
        hat = Hat.objects.get(name=hat_name)
        # test that this option is not available for an other user
        self.client.force_login(ProfileFactory().user)
        result = self.client.post(reverse("remove-hat", args=[user.pk, hat.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        self.assertIn(hat, profile.hats.all())
        # but check that it works for the user having the hat
        self.client.force_login(user)
        result = self.client.post(reverse("remove-hat", args=[user.pk, hat.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(hat, profile.hats.all())
        # test that it works for a staff member
        profile.hats.add(hat)  # we have to add the hat again for this test
        self.client.force_login(self.staff)
        result = self.client.post(reverse("remove-hat", args=[user.pk, hat.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(hat, profile.hats.all())
        # but check that the hat still exists in database
        self.assertTrue(Hat.objects.filter(name=hat_name).exists())

    def test_hats_settings(self):
        hat_name = "A hat"
        other_hat_name = "Another hat"
        hat, _ = Hat.objects.get_or_create(name__iexact=hat_name, defaults={"name": hat_name})
        requests_count = HatRequest.objects.count()
        profile = ProfileFactory()
        profile.hats.add(hat)
        # login and check that the hat appears
        self.client.force_login(profile.user)
        result = self.client.get(reverse("hats-settings"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, hat_name)
        # check that it's impossible to ask for a hat the user already has
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(HatRequest.objects.count(), requests_count)  # request wasn't sent
        # ask for another hat
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": other_hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(HatRequest.objects.count(), requests_count + 1)  # request was sent!
        # check the request appears
        result = self.client.get(reverse("hats-settings"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, other_hat_name)
        # and check it's impossible to ask for it again
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": other_hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(HatRequest.objects.count(), requests_count + 1)  # request wasn't sent
        # check that it's impossible to ask for a hat linked to a group
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": "Staff",
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(HatRequest.objects.count(), requests_count + 1)  # request wasn't sent

    def test_requested_hats(self):
        hat_name = "A hat"
        # ask for a hat
        profile = ProfileFactory()
        self.client.force_login(profile.user)
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        # test this page is only available for staff
        result = self.client.get(reverse("requested-hats"))
        self.assertEqual(result.status_code, 403)
        # login as staff
        self.client.force_login(self.staff)
        # test the count displayed on the user menu is right
        requests_count = HatRequest.objects.count()
        result = self.client.get(reverse("pages-index"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, f"({requests_count})")
        # test that the hat asked appears on the requested hats page
        result = self.client.get(reverse("requested-hats"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, hat_name)

    def test_hat_request_detail(self):
        hat_name = "A hat"
        # ask for a hat
        profile = ProfileFactory()
        self.client.force_login(profile.user)
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        request = HatRequest.objects.latest("date")
        # test this page is available for the request author
        result = self.client.get(request.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        # test it's not available for another user
        other_user = ProfileFactory().user
        self.client.force_login(other_user)
        result = self.client.get(request.get_absolute_url())
        self.assertEqual(result.status_code, 403)
        # login as staff
        self.client.force_login(self.staff)
        # test the page works
        result = self.client.get(request.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, hat_name)
        self.assertContains(result, profile.user.username)
        self.assertContains(result, request.reason)

    def test_solve_hat_request(self):
        hat_name = "A hat"
        # ask for a hat
        profile = ProfileFactory()
        self.client.force_login(profile.user)
        result = self.client.post(
            reverse("hats-settings"),
            {
                "hat": hat_name,
                "reason": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        request = HatRequest.objects.latest("date")
        # test this page is only available for staff
        result = self.client.post(reverse("solve-hat-request", args=[request.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        # test denying as staff
        self.client.force_login(self.staff)
        result = self.client.post(reverse("solve-hat-request", args=[request.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotIn(hat_name, [h.name for h in profile.hats.all()])
        request = HatRequest.objects.get(pk=request.pk)  # reload
        self.assertEqual(request.is_granted, False)
        # add a new request and test granting
        HatRequest.objects.create(user=profile.user, hat=hat_name, reason="test")
        request = HatRequest.objects.latest("date")
        result = self.client.post(reverse("solve-hat-request", args=[request.pk]), {"grant": "on"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertIn(hat_name, [h.name for h in profile.hats.all()])
        request = HatRequest.objects.get(pk=request.pk)  # reload
        self.assertEqual(request.is_granted, True)

    def test_hats_list(self):
        # test the page is accessible without being authenticated
        self.client.logout()
        result = self.client.get(reverse("hats-list"))
        self.assertEqual(result.status_code, 200)
        # and while being authenticated
        self.client.force_login(self.staff)
        result = self.client.get(reverse("hats-list"))
        self.assertEqual(result.status_code, 200)
        # test that it does contain the name of a hat
        self.assertContains(result, "Staff")  # this hat hat was created with the staff user

    def test_hat_detail(self):
        # we will use the staff hat, created with the staff user
        hat = Hat.objects.get(name="Staff")
        # test the page is accessible without being authenticated
        self.client.logout()
        result = self.client.get(hat.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        # and while being authenticated
        self.client.force_login(self.staff)
        result = self.client.get(hat.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        # test that it does contain the name of a hat
        self.assertContains(result, hat.name)
        # and the name of a user having it
        self.client.logout()  # to prevent the username from being shown in topbar
        result = self.client.get(hat.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, self.staff.username)
        # if we display this group on the contact page...
        GroupContact.objects.create(group=Group.objects.get(name="staff"), description="group description", position=1)
        # the description should be shown on this page too
        result = self.client.get(hat.get_absolute_url())
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "group description")
