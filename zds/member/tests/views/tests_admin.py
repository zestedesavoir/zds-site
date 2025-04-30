from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, TopicFactory
from zds.member.models import Profile
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.notification.models import TopicAnswerSubscription


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

    def test_promote_interface(self):
        """
        Test promotion interface.
        """

        # create users (one regular, one staff and one superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()
        tester.user.is_active = False
        tester.user.save()
        staff.user.is_superuser = True
        staff.user.save()

        # create groups
        group = Group.objects.create(name="DummyGroup_1")
        groupbis = Group.objects.create(name="DummyGroup_2")

        # create Forums, Posts and subscribe member to them.
        category1 = ForumCategoryFactory(position=1)
        forum1 = ForumFactory(category=category1, position_in_category=1)
        forum1.groups.add(group)
        forum1.save()
        forum2 = ForumFactory(category=category1, position_in_category=2)
        forum2.groups.add(groupbis)
        forum2.save()
        forum3 = ForumFactory(category=category1, position_in_category=3)
        topic1 = TopicFactory(forum=forum1, author=staff.user)
        topic2 = TopicFactory(forum=forum2, author=staff.user)
        topic3 = TopicFactory(forum=forum3, author=staff.user)

        # LET THE TEST BEGIN !

        # At this point, the user cannot log in because the account is inactive.
        # This behavior is tested in the tests of LoginView.

        # connect as staff (superuser)
        self.client.force_login(staff.user)

        # check that we can go through the page
        result = self.client.get(reverse("member-settings-promote", kwargs={"user_pk": tester.user.id}), follow=False)
        self.assertEqual(result.status_code, 200)

        # give groups thanks to staff (but account still not activated)
        result = self.client.post(
            reverse("member-settings-promote", kwargs={"user_pk": tester.user.id}),
            {
                "groups": [group.id, groupbis.id],
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 2)
        self.assertFalse(tester.user.is_active)

        # Now our tester is going to follow one post in every forum (3)
        TopicAnswerSubscription.objects.toggle_follow(topic1, tester.user)
        TopicAnswerSubscription.objects.toggle_follow(topic2, tester.user)
        TopicAnswerSubscription.objects.toggle_follow(topic3, tester.user)

        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 3)

        # retract all rights, keep one group only and activate account
        result = self.client.post(
            reverse("member-settings-promote", kwargs={"user_pk": tester.user.id}),
            {"groups": [group.id], "activation": "on"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 1)
        self.assertTrue(tester.user.is_active)
        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 2)

        # no groups specified
        result = self.client.post(
            reverse("member-settings-promote", kwargs={"user_pk": tester.user.id}), {"activation": "on"}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh
        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 1)

        # Finally, check that the user cannot access the interface.
        tester_from_db = User.objects.get(username=tester.user.username)
        self.assertTrue(tester_from_db.is_active)
        self.client.force_login(tester.user)
        result = self.client.post(
            reverse("member-settings-promote", kwargs={"user_pk": staff.user.id}), {"activation": "on"}, follow=False
        )
        self.assertEqual(result.status_code, 403)  # forbidden !
