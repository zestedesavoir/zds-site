from copy import deepcopy

from django.conf import settings
from django.urls import reverse
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

from zds.forum.factories import ForumCategoryFactory, ForumFactory
from zds.forum.models import Topic
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.notification.models import (
    NewTopicSubscription,
    Notification,
    NewPublicationSubscription,
    ContentReactionAnswerSubscription,
    PingSubscription,
)
from zds.tutorialv2 import signals
from zds.tutorialv2.factories import (
    PublishableContentFactory,
    PublishedContentFactory,
    ContentReactionFactory,
)
from zds.tutorialv2.publication_utils import publish_content, notify_update
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.utils.factories import SubCategoryFactory, LicenceFactory
from zds.utils.mps import send_mp, send_message_mp
from zds.utils.header_notifications import get_header_notifications

overridden_zds_app = deepcopy(settings.ZDS_APP)


@override_settings(ZDS_APP=overridden_zds_app)
class ForumNotification(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.to_be_changed_staff = StaffProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.assertTrue(self.staff.has_perm("forum.change_topic"))
        self.category1 = ForumCategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)
        for group in self.staff.groups.all():
            self.forum12.groups.add(group)
        self.forum12.save()

    def test_ping_unknown(self):
        overridden_zds_app["comment"]["enable_pings"] = True
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "@anUnExistingUser is pinged, also a special chars user @{}",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302, "Request must succeed")
        self.assertEqual(
            0, PingSubscription.objects.count(), "As one user is pinged, only one subscription is created."
        )

    def test_no_auto_ping(self):
        overridden_zds_app["comment"]["enable_pings"] = True
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"@{self.user1.username} is pinged, not @{self.user2.username}",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            1, PingSubscription.objects.count(), "As one user is pinged, only one subscription is created."
        )

    def test_edit_with_more_than_max_ping(self):
        overridden_zds_app["comment"]["max_pings"] = 2
        overridden_zds_app["comment"]["enable_pings"] = True
        pinged_users = [ProfileFactory(), ProfileFactory(), ProfileFactory(), ProfileFactory()]
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "@{} @{} are pinged, not @{} @{}".format(*[a.user.username for a in pinged_users]),
                "tags": "",
            },
            follow=False,
        )
        topic = Topic.objects.last()
        post = topic.last_message
        self.assertEqual(2, PingSubscription.objects.count())
        self.assertTrue(PingSubscription.objects.get_existing(pinged_users[0].user, post, True))
        self.assertTrue(PingSubscription.objects.get_existing(pinged_users[1].user, post, True))
        self.assertFalse(PingSubscription.objects.get_existing(pinged_users[2].user, post, True))
        self.assertFalse(PingSubscription.objects.get_existing(pinged_users[3].user, post, True))
        self.client.post(
            reverse("topic-edit") + f"?topic={topic.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "@{} @{} are pinged".format(pinged_users[1].user.username, pinged_users[3].user.username),
                "tags": "",
            },
            follow=False,
        )
        self.assertTrue(PingSubscription.objects.get_existing(pinged_users[3].user, post, True))
        self.assertTrue(PingSubscription.objects.get_existing(pinged_users[1].user, post, True))
        self.assertFalse(PingSubscription.objects.get_existing(pinged_users[0].user, post, True))

    def test_no_reping_on_edition(self):
        """
        to be more accurate : on edition, only ping **new** members
        """
        overridden_zds_app["comment"]["enable_pings"] = True
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"@{self.user1.username} is pinged",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            1, PingSubscription.objects.count(), "As one user is pinged, only one subscription is created."
        )
        self.assertEqual(1, Notification.objects.count())
        user3 = ProfileFactory().user
        post = Topic.objects.last().last_message
        result = self.client.post(
            reverse("post-edit") + f"?message={post.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"@{self.user1.username} is pinged even twice @{self.user1.username}",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(1, PingSubscription.objects.count(), "No added subscription.")
        self.assertEqual(1, Notification.objects.count())
        result = self.client.post(
            reverse("post-edit") + f"?message={post.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "@{} is pinged even twice @{} and add @{}".format(
                    self.user1.username, self.user1.username, user3.username
                ),
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(2, PingSubscription.objects.count())
        self.assertEqual(2, Notification.objects.count())

    def test_loose_ping_on_edition(self):
        """
        to be more accurate : on edition, only ping **new** members
        """
        overridden_zds_app["comment"]["enable_pings"] = True
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"@{self.user1.username} is pinged",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            1, PingSubscription.objects.count(), "As one user is pinged, only one subscription is created."
        )
        self.assertEqual(1, Notification.objects.count())
        post = Topic.objects.last().last_message
        result = self.client.post(
            reverse("post-edit") + f"?message={post.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"@ {self.user1.username} is no more pinged ",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(1, PingSubscription.objects.count(), "No added subscription.")
        self.assertFalse(PingSubscription.objects.first().is_active)
        self.assertEqual(1, Notification.objects.count())
        self.assertTrue(Notification.objects.first().is_read)

    def test_no_dead_notif_on_moving(self):
        NewTopicSubscription.objects.get_or_create_active(self.user1, self.forum11)
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "En tout cas l'un abonnement",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title="Super sujet").first()
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.assertIsNotNone(subscription.last_notification, "There must be a notification for now")
        self.assertFalse(subscription.last_notification.is_read)
        self.client.logout()
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        data = {"move": "", "forum": self.forum12.pk, "topic": topic.pk}
        response = self.client.post(reverse("topic-edit"), data, follow=False)
        self.assertEqual(302, response.status_code)
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, "There must still be an active subscription")
        self.assertIsNotNone(
            subscription.last_notification, "There must still be a notification as object is not removed."
        )
        self.assertEqual(subscription.last_notification, Notification.objects.filter(sender=self.user2).first())
        self.assertTrue(subscription.last_notification.is_read, "As forum is not reachable, notification is read")

    def test_no_ping_on_private_forum(self):
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"ping @{self.user1.username}",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title="Super sujet").first()
        subscription = PingSubscription.objects.get_existing(self.user1, topic.last_message, True)
        self.assertIsNone(subscription, "There must be no active subscription for now")

    def test_no_dead_ping_notif_on_moving_to_private_forum(self):
        self.assertTrue(self.client.login(username=self.user2.username, password="hostel77"))
        result = self.client.post(
            reverse("topic-new") + f"?forum={self.forum11.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": f"ping @{self.user1.username}",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title="Super sujet").first()
        subscription = PingSubscription.objects.get_existing(self.user1, topic.last_message, True)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.assertIsNotNone(subscription.last_notification, "There must be a notification for now")
        self.assertFalse(subscription.last_notification.is_read)
        self.client.logout()
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        data = {"move": "", "forum": self.forum12.pk, "topic": topic.pk}
        response = self.client.post(reverse("topic-edit"), data, follow=False)
        self.assertEqual(302, response.status_code)
        subscription = PingSubscription.objects.get_existing(self.user1, topic.last_message, True)
        self.assertIsNotNone(subscription, "There must still be an active subscription")
        self.assertIsNotNone(
            subscription.last_notification, "There must still be a notification as object is not removed."
        )
        self.assertEqual(subscription.last_notification, Notification.objects.filter(sender=self.user2).first())
        self.assertTrue(subscription.last_notification.is_read, "As forum is not reachable, notification is read")

    def test_no_more_notif_on_losing_all_groups(self):
        NewTopicSubscription.objects.get_or_create_active(self.to_be_changed_staff, self.forum12)
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        self.client.post(
            reverse("topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "En tout cas l'un abonnement",
                "tags": "",
            },
            follow=False,
        )
        subscription = NewTopicSubscription.objects.get_existing(self.to_be_changed_staff, self.forum12, True)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.to_be_changed_staff.groups.clear()
        self.to_be_changed_staff.save()
        subscription = NewTopicSubscription.objects.get_existing(self.to_be_changed_staff, self.forum12, False)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.assertFalse(subscription.is_active)

    def test_no_more_notif_on_losing_one_group(self):
        NewTopicSubscription.objects.get_or_create_active(self.to_be_changed_staff, self.forum12)
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        self.client.post(
            reverse("topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Super sujet",
                "subtitle": "Pour tester les notifs",
                "text": "En tout cas l'un abonnement",
                "tags": "",
            },
            follow=False,
        )
        subscription = NewTopicSubscription.objects.get_existing(self.to_be_changed_staff, self.forum12, True)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.to_be_changed_staff.groups.remove(list(self.to_be_changed_staff.groups.all())[0])
        self.to_be_changed_staff.save()
        subscription = NewTopicSubscription.objects.get_existing(self.to_be_changed_staff, self.forum12, False)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.assertFalse(subscription.is_active)


@override_for_contents()
class ContentNotification(TestCase, TutorialTestMixin):
    def setUp(self):

        # don't build PDF to speed up the tests
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user1)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user1, mode="W")
        self.tuto.licence = LicenceFactory()
        self.tuto.subcategory.add(SubCategoryFactory())
        self.tuto.save()
        tuto_draft = self.tuto.load_version()

        # then, publish it !
        version = tuto_draft.current_version
        self.published = publish_content(self.tuto, tuto_draft, is_major_update=True)

        self.tuto.sha_public = version
        self.tuto.sha_draft = version
        self.tuto.public_version = self.published
        self.tuto.save()

        self.assertTrue(self.client.login(username=self.user1.username, password="hostel77"))

    def test_no_persistant_notif_on_revoke(self):
        from zds.tutorialv2.publication_utils import unpublish_content

        NewPublicationSubscription.objects.get_or_create_active(self.user1, self.user2)
        content = PublishedContentFactory(author_list=[self.user2])

        signals.content_published.send(sender=self.tuto.__class__, instance=content, by_email=False)
        self.assertEqual(1, len(Notification.objects.get_notifications_of(self.user1)))
        unpublish_content(content)
        self.assertEqual(0, len(Notification.objects.get_notifications_of(self.user1)))

    def test_no_persistant_comment_notif_on_revoke(self):
        from zds.tutorialv2.publication_utils import unpublish_content

        content = PublishedContentFactory(author_list=[self.user2])
        ContentReactionAnswerSubscription.objects.get_or_create_active(self.user1, content)
        ContentReactionFactory(related_content=content, author=self.user2, position=1)
        self.assertEqual(1, len(Notification.objects.get_unread_notifications_of(self.user1)))
        unpublish_content(content, moderator=self.user2)
        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user1)))

    def test_only_one_notif_on_update(self):
        NewPublicationSubscription.objects.get_or_create_active(self.user1, self.user2)
        content = PublishedContentFactory(author_list=[self.user2])
        notify_update(content, False, True)
        versioned = content.load_version()
        content.sha_draft = versioned.repo_update(
            introduction="new intro", conclusion="new conclusion", title=versioned.title
        )
        content.save()
        publish_content(content, content.load_version(), True)
        notify_update(content, True, False)
        notifs = get_header_notifications(self.user1)["general_notifications"]["list"]
        self.assertEqual(1, len(notifs), str(notifs))

    def test_only_one_notif_on_major_update(self):
        NewPublicationSubscription.objects.get_or_create_active(self.user1, self.user2)
        content = PublishedContentFactory(author_list=[self.user2])
        notify_update(content, False, True)
        versioned = content.load_version()
        content.sha_draft = versioned.repo_update(
            introduction="new intro", conclusion="new conclusion", title=versioned.title
        )
        content.save()
        publish_content(content, content.load_version(), True)
        notify_update(content, True, True)
        notifs = get_header_notifications(self.user1)["general_notifications"]["list"]
        self.assertEqual(1, len(notifs), str(notifs))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SubscriptionsTest(TestCase):
    def setUp(self):
        self.userStandard1 = ProfileFactory(email_for_answer=True, email_for_new_mp=True).user
        self.userOAuth1 = ProfileFactory(email_for_answer=True, email_for_new_mp=True).user
        self.userOAuth2 = ProfileFactory(email_for_answer=True, email_for_new_mp=True).user

        self.userOAuth1.email = ""
        self.userOAuth2.email = "this is not an email"

        self.userOAuth1.save()
        self.userOAuth2.save()

    def test_no_emails_for_those_who_have_none(self):
        """
        Test that we do not try to send e-mails to those who have not registered one.
        """
        self.assertEqual(0, len(mail.outbox))
        topic = send_mp(
            author=self.userStandard1,
            users=[self.userOAuth1],
            title="Testing",
            subtitle="",
            text="",
            send_by_mail=True,
            leave=False,
        )

        self.assertEqual(0, len(mail.outbox))

        send_message_mp(self.userOAuth1, topic, "", send_by_mail=True)

        self.assertEqual(1, len(mail.outbox))

    def test_no_emails_for_those_who_have_other_things_in_that_place(self):
        """
        Test that we do not try to send e-mails to those who have not registered a valid one.
        """
        self.assertEqual(0, len(mail.outbox))
        topic = send_mp(
            author=self.userStandard1,
            users=[self.userOAuth2],
            title="Testing",
            subtitle="",
            text="",
            send_by_mail=True,
            leave=False,
        )

        self.assertEqual(0, len(mail.outbox))

        send_message_mp(self.userOAuth2, topic, "", send_by_mail=True)

        self.assertEqual(1, len(mail.outbox))
