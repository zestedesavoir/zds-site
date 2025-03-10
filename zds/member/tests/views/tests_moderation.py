from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.member.models import Ban, KarmaNote, Profile
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.member.views.moderation import member_from_ip
from zds.notification.models import Notification


class TestsModeration(TestCase):
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

    def test_ls_followed_by_unls(self):
        """
        Test various sanctions.
        """

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        # list of members.
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context["members"])

        # Test: LS
        user_ls = ProfileFactory()
        ls_text = "Texte de test pour LS"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": user_ls.user.id}),
            {"ls": "", "ls-text": ls_text},
            follow=False,
        )
        profile = Profile.objects.get(id=user_ls.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-pubdate")[0]
        self.assertEqual(ban.type, "Lecture seule illimitée")
        self.assertEqual(ban.note, ls_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 1)
        self.assertEqual(Notification.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # LS guy still shows up, good

        # Test: Un-LS
        unls_text = "Texte de test pour un-LS"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": user_ls.user.id}),
            {"un-ls": "", "unls-text": unls_text},
            follow=False,
        )
        profile = Profile.objects.get(id=user_ls.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertEqual(ban.type, "Levée de la lecture seule")
        self.assertEqual(ban.note, unls_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # LS guy still shows up, good

    def test_temp_ban_missing_duration(self):
        # Test error is caught when the duration for temporary sanction is missing in submitted form.
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        profile = ProfileFactory()
        ls_text = "Texte de test pour LS TEMP"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"ls-temp": "", "ls-text": ls_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

    def test_temp_ls_followed_by_unls(self):
        """
        Test various sanctions.
        """

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        # list of members.
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context["members"])

        # Test: Temp LS
        profile = ProfileFactory()
        ls_text = "Texte de test pour LS TEMP"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"ls-temp": "", "ls-jrs": 10, "ls-text": ls_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNotNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertIn("Lecture seule temporaire", ban.type)
        self.assertEqual(ban.note, ls_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 1)
        self.assertEqual(Notification.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # LS guy still shows up, good

        # Test: Un-LS
        unls_text = "Texte de test pour un-LS"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"un-ls": "", "unls-text": unls_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertEqual(ban.type, "Levée de la lecture seule")
        self.assertEqual(ban.note, unls_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # LS guy still shows up, good

    def test_ban_followed_by_unban(self):
        """
        Test ban followed by unban.
        """

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        # list of members.
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context["members"])

        # Test: BAN
        profile = ProfileFactory()
        ban_text = "Texte de test pour BAN"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"ban": "", "ban-text": ban_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertFalse(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertEqual(ban.type, "Bannissement illimité")
        self.assertEqual(ban.note, ban_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context["members"]))  # Banned guy doesn't show up, good

        # Test: un-BAN
        unban_text = "Texte de test pour UNBAN"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"un-ban": "", "unban-text": unban_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertEqual(ban.type, "Levée du bannissement")
        self.assertEqual(ban.note, unban_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # UnBanned guy shows up, good

    def test_temp_ban_followed_by_unban(self):
        """
        Test temporary ban followed by unban.
        """

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        # list of members.
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context["members"])

        # Test: BAN
        profile = ProfileFactory()
        ban_text = "Texte de test pour BAN TEMP"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"ban-temp": "", "ban-jrs": 10, "ban-text": ban_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertFalse(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNotNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertIn("Bannissement temporaire", ban.type)
        self.assertEqual(ban.note, ban_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context["members"]))  # Banned guy doesn't show up, good

        # Test: un-BAN
        unban_text = "Texte de test pour UNBAN"
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": profile.user.id}),
            {"un-ban": "", "unban-text": unban_text},
            follow=False,
        )
        profile = Profile.objects.get(id=profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(profile.can_write)
        self.assertTrue(profile.can_read)
        self.assertIsNone(profile.end_ban_write)
        self.assertIsNone(profile.end_ban_read)
        ban = Ban.objects.filter(user__id=profile.user.id).order_by("-id")[0]
        self.assertEqual(ban.type, "Levée du bannissement")
        self.assertEqual(ban.note, unban_text)
        self.assertEqual(Notification.objects.filter(subscription__user=profile.user, is_read=False).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users + 1, len(result.context["members"]))  # UnBanned guy shows up, good

    def test_sanctions_with_not_staff_user(self):
        user = ProfileFactory().user

        # we need staff right for update the sanction of a user, so a member who is not staff can't access to the page
        self.client.logout()
        self.client.force_login(user)

        # Test: LS
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": self.staff.id}),
            {"ls": "", "ls-text": "Texte de test pour LS"},
            follow=False,
        )

        self.assertEqual(result.status_code, 403)

        # if the user is staff, he can update the sanction of a user
        self.client.logout()
        self.client.force_login(self.staff)

        # Test: LS
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": user.id}),
            {"ls": "", "ls-text": "Texte de test pour LS"},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

    def test_failed_bot_sanctions(self):
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)

        bot_profile = ProfileFactory()
        bot_profile.user.groups.add(self.bot)
        bot_profile.user.save()

        # Test: LS
        result = self.client.post(
            reverse("member-modify-profile", kwargs={"user_pk": bot_profile.user.id}),
            {"ls": "", "ls-text": "Texte de test pour LS"},
            follow=False,
        )
        user = Profile.objects.get(id=bot_profile.id)  # Refresh profile from DB
        self.assertEqual(result.status_code, 403)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)

    def test_karma(self):
        user = ProfileFactory()
        other_user = ProfileFactory()
        self.client.force_login(other_user.user)
        r = self.client.post(reverse("member-modify-karma"), {"profile_pk": user.pk, "karma": 42, "note": "warn"})
        self.assertEqual(403, r.status_code)
        self.client.logout()
        self.client.force_login(self.staff)
        # bad id
        r = self.client.post(
            reverse("member-modify-karma"), {"profile_pk": "blah", "karma": 42, "note": "warn"}, follow=True
        )
        self.assertEqual(404, r.status_code)
        # good karma
        r = self.client.post(
            reverse("member-modify-karma"), {"profile_pk": user.pk, "karma": 42, "note": "warn"}, follow=True
        )
        self.assertEqual(200, r.status_code)
        self.assertIn("{} : 42".format(_("Modification du karma")), r.content.decode("utf-8"))
        # more than 100 karma must unvalidate the karma
        r = self.client.post(
            reverse("member-modify-karma"), {"profile_pk": user.pk, "karma": 420, "note": "warn"}, follow=True
        )
        self.assertEqual(200, r.status_code)
        self.assertNotIn("{} : 420".format(_("Modification du karma")), r.content.decode("utf-8"))
        # empty warning must unvalidate the karma
        r = self.client.post(
            reverse("member-modify-karma"), {"profile_pk": user.pk, "karma": 41, "note": ""}, follow=True
        )
        self.assertEqual(200, r.status_code)
        self.assertNotIn("{} : 41".format(_("Modification du karma")), r.content.decode("utf-8"))

    def test_modify_user_karma(self):
        """
        To test karma of a user modified by a staff user.
        """
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # login as user
        result = self.client.post(
            reverse("member-login"), {"username": tester.user.username, "password": "hostel77"}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # check that user can't use this feature
        result = self.client.post(reverse("member-modify-karma"), follow=False)
        self.assertEqual(result.status_code, 403)

        # login as staff
        result = self.client.post(
            reverse("member-login"), {"username": staff.user.username, "password": "hostel77"}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # try to give a few bad points to the tester
        result = self.client.post(
            reverse("member-modify-karma"),
            {"profile_pk": tester.pk, "note": "Bad tester is bad !", "karma": "-50"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -50)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 1)

        # Now give a few good points
        result = self.client.post(
            reverse("member-modify-karma"),
            {"profile_pk": tester.pk, "note": "Good tester is good !", "karma": "10"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 2)

        # Now access some unknow user
        result = self.client.post(
            reverse("member-modify-karma"),
            {"profile_pk": 9999, "note": "Good tester is good !", "karma": "10"},
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # Now give unknow point
        result = self.client.post(
            reverse("member-modify-karma"),
            {"profile_pk": tester.pk, "note": "Good tester is good !", "karma": ""},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 3)

        # Now give no point at all
        result = self.client.post(
            reverse("member-modify-karma"), {"profile_pk": tester.pk, "note": "Good tester is good !"}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 4)

        # Now access without post
        result = self.client.get(reverse("member-modify-karma"), follow=False)
        self.assertEqual(result.status_code, 405)

    def test_karma_and_pseudo_change(self):
        """
        To test that a karma note is added when a member change its pseudo
        """
        tester = ProfileFactory()
        old_pseudo = tester.user.username
        self.client.force_login(tester.user)
        data = {"username": "dummy", "email": tester.user.email, "password": "hostel77"}
        result = self.client.post(reverse("update-username-email-member"), data, follow=False)

        self.assertEqual(result.status_code, 302)
        notes = KarmaNote.objects.filter(user=tester.user).all()
        self.assertEqual(len(notes), 1)
        self.assertTrue(old_pseudo in notes[0].note and "dummy" in notes[0].note)

    def test_moderation_history(self):
        user = ProfileFactory().user

        ban = Ban(
            user=user,
            moderator=self.staff,
            type="Lecture Seule Temporaire",
            note="Test de LS",
            pubdate=datetime.now(),
        )
        ban.save()

        note = KarmaNote(
            user=user,
            moderator=self.staff,
            karma=5,
            note="Test de karma",
            pubdate=datetime.now(),
        )
        note.save()

        # staff rights are required to view the history, check that
        self.client.logout()
        self.client.force_login(user)
        result = self.client.get(user.profile.get_absolute_url(), follow=False)
        self.assertNotContains(result, "Historique de modération")

        self.client.logout()
        self.client.force_login(self.staff)
        result = self.client.get(user.profile.get_absolute_url(), follow=False)
        self.assertContains(result, "Historique de modération")

        # check that the note and the sanction are in the context
        self.assertIn(ban, result.context["actions"])
        self.assertIn(note, result.context["actions"])

        # and are displayed
        self.assertContains(result, "Test de LS")
        self.assertContains(result, "Test de karma")

    def test_filter_member_ip(self):
        """
        Test filter member by ip.
        """

        # create users (one regular and one staff and superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # test login normal user
        result = self.client.post(
            reverse("member-login"),
            {"username": tester.user.username, "password": "hostel77", "remember": "remember"},
            follow=False,
        )
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # Check that the filter can't be access from normal user
        result = self.client.post(
            reverse("member-from-ip", kwargs={"ip_address": tester.last_ip_address}), {}, follow=False
        )
        self.assertEqual(result.status_code, 403)

        # log the staff user
        result = self.client.post(
            reverse("member-login"),
            {"username": staff.user.username, "password": "hostel77", "remember": "remember"},
            follow=False,
        )
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # test that we retrieve correctly the 2 members (staff + user) from this ip
        result = self.client.post(
            reverse("member-from-ip", kwargs={"ip_address": staff.last_ip_address}), {}, follow=False
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["members"]), 2)


class IpListingsTests(TestCase):
    """Test the member_from_ip view: listing users from a same IPv4/IPv6 address or same IPv6 network."""

    def setUp(self) -> None:
        self.staff = StaffProfileFactory().user
        self.regular_user = ProfileFactory()

        self.user_ipv4_same_ip_1 = ProfileFactory(last_ip_address="155.128.92.54")
        self.user_ipv4_same_ip_1.user.username = "user_ipv4_same_ip_1"
        self.user_ipv4_same_ip_1.user.save()

        self.user_ipv4_same_ip_2 = ProfileFactory(last_ip_address="155.128.92.54")
        self.user_ipv4_same_ip_2.user.username = "user_ipv4_same_ip_2"
        self.user_ipv4_same_ip_2.user.save()

        self.user_ipv4_different_ip = ProfileFactory(last_ip_address="155.128.92.55")
        self.user_ipv4_different_ip.user.username = "user_ipv4_different_ip"
        self.user_ipv4_different_ip.user.save()

        self.user_ipv6_same_ip_1 = ProfileFactory(last_ip_address="2001:8f8:1425:60a0:7981:9852:1493:3721")
        self.user_ipv6_same_ip_1.user.username = "user_ipv6_same_ip_1"
        self.user_ipv6_same_ip_1.user.save()

        self.user_ipv6_same_ip_2 = ProfileFactory(last_ip_address="2001:8f8:1425:60a0:7981:9852:1493:3721")
        self.user_ipv6_same_ip_2.user.username = "user_ipv6_same_ip_2"
        self.user_ipv6_same_ip_2.user.save()

        self.user_ipv6_same_network = ProfileFactory(last_ip_address="2001:8f8:1425:60a0:9852:7981:3721:1493")
        self.user_ipv6_same_network.user.username = "user_ipv6_same_network"
        self.user_ipv6_same_network.user.save()

        self.user_ipv6_different_network = ProfileFactory(last_ip_address="8f8:60a0:3721:1425:7981:1493:2001:9852")
        self.user_ipv6_different_network.user.username = "user_ipv6_different_network"
        self.user_ipv6_different_network.user.save()

    def test_same_ipv4(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=[self.user_ipv4_same_ip_1.last_ip_address]))
        self.assertContains(response, self.user_ipv4_same_ip_1.user.username)
        self.assertContains(response, self.user_ipv4_same_ip_2.user.username)
        self.assertContains(response, self.user_ipv4_same_ip_1.last_ip_address)
        self.assertNotContains(response, self.user_ipv4_different_ip.user.username)

    def test_different_ipv4(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=[self.user_ipv4_different_ip.last_ip_address]))
        self.assertContains(response, self.user_ipv4_different_ip.user.username)
        self.assertContains(response, self.user_ipv4_different_ip.last_ip_address)
        self.assertNotContains(response, self.user_ipv6_same_ip_1.user.username)

    def test_same_ipv6_and_same_ipv6_network(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=[self.user_ipv6_same_ip_1.last_ip_address]))
        self.assertContains(response, self.user_ipv6_same_ip_1.user.username)
        self.assertContains(response, self.user_ipv6_same_ip_2.user.username)
        self.assertContains(response, self.user_ipv6_same_network.user.username)
        self.assertNotContains(response, self.user_ipv6_different_network.user.username)

    def test_same_ipv6_network_but_different_ip(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=[self.user_ipv6_same_network.last_ip_address]))
        self.assertContains(response, self.user_ipv6_same_network.user.username)
        self.assertContains(response, self.user_ipv6_same_ip_1.user.username)
        self.assertContains(response, self.user_ipv6_same_ip_2.user.username)
        self.assertNotContains(response, self.user_ipv6_different_network.user.username)

    def test_different_ipv6_network(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=[self.user_ipv6_different_network.last_ip_address]))
        self.assertContains(response, self.user_ipv6_different_network.user.username)
        self.assertNotContains(response, self.user_ipv6_same_ip_1.user.username)
        self.assertNotContains(response, self.user_ipv6_same_ip_2.user.username)
        self.assertNotContains(response, self.user_ipv6_same_network.user.username)

    def test_ip_page_invalid_ip(self) -> None:
        self.client.force_login(self.staff)
        for ip in ["foo", "340.340.340.340", "2402:4899:1c8a:d75a:"]:
            with self.subTest(ip):
                response = self.client.get(reverse(member_from_ip, args=[ip]))
                self.assertEqual(response.status_code, 404)

    def test_access_rights_to_ip_page_as_regular_user(self) -> None:
        self.client.force_login(self.regular_user.user)
        response = self.client.get(reverse(member_from_ip, args=["0.0.0.0"]))
        self.assertEqual(response.status_code, 403)

    def test_access_rights_to_ip_page_as_anonymous(self) -> None:
        response = self.client.get(reverse(member_from_ip, args=["0.0.0.0"]))
        self.assertEqual(response.status_code, 302)

    def test_access_rights_to_ip_page_as_staff(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=["0.0.0.0"]))
        self.assertEqual(response.status_code, 200)

    def test_template_used_by_ip_page(self) -> None:
        self.client.force_login(self.staff)
        response = self.client.get(reverse(member_from_ip, args=["0.0.0.0"]))
        self.assertTemplateUsed(response, "member/admin/memberip.html")
