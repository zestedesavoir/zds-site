import copy
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from zds.forum.models import Topic
from zds.forum.tests.factories import (
    ForumCategoryFactory,
    ForumFactory,
    PostFactory,
    TagFactory,
    TopicFactory,
    create_category_and_forum,
)
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import mark_read
from zds.mp.utils import send_message_mp, send_mp
from zds.notification.models import (
    ContentReactionAnswerSubscription,
    NewPublicationSubscription,
    NewTopicSubscription,
    Notification,
    PrivateTopicAnswerSubscription,
    TopicAnswerSubscription,
)
from zds.tutorialv2 import signals
from zds.tutorialv2.models.database import ContentReaction, PublishableContent
from zds.tutorialv2.publication_utils import notify_update, publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContentReactionFactory, PublishableContentFactory, PublishedContentFactory
from zds.utils import old_slugify
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


class NotificationForumTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        self.category1 = ForumCategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)

        self.tag1 = TagFactory(title="Linux")
        self.tag2 = TagFactory(title="Windows")

        self.client.force_login(self.user1)

    def test_creation_topic(self):
        """
        When we create a topic, the author follows it.
        """
        result = self.client.post(
            reverse("forum:topic-new") + f"?forum={self.forum12.pk}",
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
        content_type = ContentType.objects.get_for_model(topic)

        subscription = TopicAnswerSubscription.objects.get(
            object_id=topic.pk, content_type__pk=content_type.pk, user=self.user1
        )
        self.assertEqual(subscription.is_active, True)

    def test_mark_read_a_topic_from_view_list_posts(self):
        """
        To ensure we can subscribe to a topic, we first generate a new notification when
        another user posts a message, then mark the notification as read after displaying
        the list of messages.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)

        # Follow the topic.
        self.assertIsNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic))
        subscription = TopicAnswerSubscription.objects.get_or_create_active(self.user1, topic)

        # Creates a new post in the topic to generate a new notification.
        PostFactory(topic=topic, author=self.user2, position=1)
        content_notification_type = ContentType.objects.get_for_model(topic.last_message)
        notification = Notification.objects.get(
            subscription=subscription,
            content_type__pk=content_notification_type.pk,
            object_id=topic.last_message.pk,
            is_read=False,
        )
        self.assertIsNotNone(notification)

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertEqual(response.status_code, 200)

        # Checks that the notification is reading now.
        notification = Notification.objects.get(
            subscription=subscription,
            content_type__pk=content_notification_type.pk,
            object_id=topic.last_message.pk,
            is_read=True,
        )
        self.assertIsNotNone(notification)

    def test_answer_topic(self):
        """
        When a user posts on a topic, a subscription to the said topic is created
        for this user.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)

        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        # check that topic creator has been notified
        notification = Notification.objects.get(subscription__user=self.user2)
        subscription_content_type = ContentType.objects.get_for_model(topic1)

        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.subscription.content_type, subscription_content_type)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

        # check that answerer has subscribed to the topic
        subscription = TopicAnswerSubscription.objects.get(
            object_id=topic1.pk, content_type__pk=subscription_content_type.pk, user=self.user1
        )
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When we post on a topic, a notification is created for each subscriber. We can
        read a notification when we display the list of messages of the said topic.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)

        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__user=self.user2)
        self.assertEqual(notification.is_read, False)

        self.client.logout()
        self.client.force_login(self.user2)

        result = self.client.get(
            reverse("forum:topic-posts-list", args=[topic1.pk, old_slugify(topic1.title)]), follow=True
        )
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__user=self.user2)
        self.assertEqual(notification.is_read, True)

    def test_subscription_deactivated_and_notification_read_when_topic_moved(self):
        """
        When a topic is moved to a forum where subscribers can't read it, the subscriptions
        should be deactivated and notifications marked as read.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        other_user = ProfileFactory().user
        TopicAnswerSubscription.objects.toggle_follow(topic, other_user)
        PostFactory(topic=topic, author=ProfileFactory().user, position=2)

        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic, is_active=True))
        self.assertIsNotNone(Notification.objects.get(subscription__user=self.user1, is_read=False))

        forum_not_read = ForumFactory(category=self.category1, position_in_category=2)
        forum_not_read.groups.add(Group.objects.create(name="DummyGroup_1"))

        self.client.force_login(StaffProfileFactory().user)
        data = {"move": "", "forum": forum_not_read.pk, "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic, is_active=False))
        self.assertIsNotNone(Notification.objects.get(subscription__user=self.user1, is_read=True))
        self.assertFalse(TopicAnswerSubscription.objects.get_existing(other_user, topic).is_active)
        self.assertIsNotNone(Notification.objects.get(subscription__user=other_user, is_read=True))

    def test_post_unread(self):
        """
        When a post is marked unread, a notification is generated.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)
        PostFactory(topic=topic1, author=self.user1, position=2)
        post = PostFactory(topic=topic1, author=self.user2, position=3)

        result = self.client.get(reverse("forum:post-unread") + f"?message={post.pk}", follow=False)

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__user=self.user1, object_id=post.pk, is_read=False)
        self.assertEqual(notification.object_id, post.pk)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

    def test_hide_post_mark_notification_as_read(self):
        """
        Ensure a notification gets deleted when the corresponding post is hidden.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        PostFactory(topic=topic, author=self.user2, position=2)
        PostFactory(topic=topic, author=ProfileFactory().user, position=3)

        notifications = Notification.objects.filter(object_id=topic.last_message.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        # hide last post
        data = {"delete_message": ""}
        self.client.force_login(StaffProfileFactory().user)
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        notifications = Notification.objects.filter(object_id=topic.last_message.pk, is_read=True).all()
        self.assertEqual(1, len(notifications))

    def test_topics_followed_by_a_user(self):
        """
        Check that we correctly retrieve all topics followed by a user.
        """
        user = UserFactory()

        topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
        self.assertEqual(0, len(topics_followed))

        first = TopicFactory(forum=self.forum11, author=user)
        second = TopicFactory(forum=self.forum11, author=user)
        third = TopicFactory(forum=self.forum11, author=user)

        # Subscribes to all topics.
        TopicAnswerSubscription.objects.get_or_create_active(user, second)
        TopicAnswerSubscription.objects.get_or_create_active(user, first)
        TopicAnswerSubscription.objects.get_or_create_active(user, third)

        topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
        self.assertEqual(3, len(topics_followed))

    def test_pubdate_on_notification_updated(self):
        """
        When we update a notification, we should update its pubdate too.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)

        topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(self.user1)
        self.assertEqual(1, len(topics_followed))

        post = PostFactory(topic=topic, author=self.user2, position=2)

        old_notification = Notification.objects.get(subscription__user=self.user1, object_id=post.pk, is_read=False)
        old_notification.pubdate = datetime.now() - timedelta(days=1)
        old_notification.save()
        self.assertEqual(old_notification.object_id, post.pk)
        self.assertEqual(old_notification.subscription.object_id, topic.pk)

        # read it.
        old_notification.is_read = True
        old_notification.save()

        user3 = UserFactory()
        post2 = PostFactory(topic=topic, author=user3, position=3)

        new_notification = Notification.objects.get(subscription__user=self.user1, object_id=post2.pk, is_read=False)
        self.assertEqual(new_notification.object_id, post2.pk)
        self.assertEqual(new_notification.subscription.object_id, topic.pk)

        # Check that the pubdate is well updated.
        self.assertTrue(old_notification.pubdate < new_notification.pubdate)

    def test_notifications_on_a_forum_subscribed(self):
        """
        When a user subscribes to a forum, they receive a notification for each topic created.
        """
        # Subscribe.
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        # Unsubscribe.
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_mark_read_a_topic_of_a_forum_subscribed(self):
        """
        When a user has a notification on a topic, the notification should be marked as read.
        """
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertEqual(response.status_code, 200)

        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_move_topic_from_forum_to_another_one(self):
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False).all()))

        # Move the topic to another forum.
        self.client.logout()
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        data = {"move": "", "forum": self.forum12.pk, "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)
        self.assertEqual(302, response.status_code)

        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(self.forum12, topic.forum)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False).all()))

        self.client.logout()
        self.client.force_login(self.user1)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=True).all()))

    def test_ping_on_tuto(self):
        """Error from #4904"""
        content = PublishedContentFactory(author_list=[self.user1])
        self.client.force_login(self.user2)
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={content.pk}",
            {
                "text": f"@{self.user1.username}",
                "last_note": 0,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(1, len(Notification.objects.filter(is_read=False).all()))

    def test_move_topic_from_forum_followed_to_forum_followed_too(self):
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)
        NewTopicSubscription.objects.toggle_follow(self.forum12, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False).all()))

        # Move the topic to another forum.
        self.client.logout()
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        data = {"move": "", "forum": self.forum12.pk, "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)
        self.assertEqual(302, response.status_code)

        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(self.forum12, topic.forum)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False, is_dead=False).all()))

        self.client.logout()
        self.client.force_login(self.user1)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=True, is_dead=False).all()))

    def test_notifications_on_a_tag_subscribed(self):
        """
        When a user subscribes to a tag, they receive a notification for each topic created.
        """
        # Subscribe.
        NewTopicSubscription.objects.toggle_follow(self.tag1, self.user1)

        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        topic1.add_tags(["Linux"])

        notifications = Notification.objects.filter(object_id=topic1.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        # Unsubscribe.
        NewTopicSubscription.objects.toggle_follow(self.tag1, self.user1)

        topic2 = TopicFactory(forum=self.forum11, author=self.user2)
        topic2.add_tags(["Linux"])
        notifications = Notification.objects.filter(object_id=topic2.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_no_notification_on_new_topic_in_hidden_forum(self):
        """
        When a user subscribes to a forum that gets hidden and a topic is created in that forum, no notification is sent
        """
        # Subscribe.
        user1 = ProfileFactory().user
        user2 = ProfileFactory().user

        group = Group.objects.create(name="Restricted")
        user2.groups.add(group)
        user2.save()
        category, forum = create_category_and_forum(group)

        NewTopicSubscription.objects.toggle_follow(forum, user1)
        topic1 = TopicFactory(forum=forum, author=user2)

        notifications = Notification.objects.filter(object_id=topic1.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_no_notification_on_a_tag_subscribed_in_hidden_forum(self):
        """
        When a user subscribes to a tag and a topic is created using that tag in a hidden forum, no notification is sent
        """
        # Subscribe.
        user1 = ProfileFactory().user
        user2 = ProfileFactory().user

        group = Group.objects.create(name="Restricted")
        user2.groups.add(group)
        user2.save()
        category, forum = create_category_and_forum(group)

        tag1 = TagFactory(title="MyTagInHiddenForum")
        NewTopicSubscription.objects.toggle_follow(tag1, user1)

        topic1 = TopicFactory(forum=forum, author=user2)
        topic1.add_tags([tag1.title])

        notifications = Notification.objects.filter(object_id=topic1.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_mark_read_a_topic_of_a_tag_subscribed(self):
        """
        When a user has a notification on a topic, the notification should be marked as read.
        """
        NewTopicSubscription.objects.toggle_follow(self.tag1, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        topic.add_tags(["Linux"])

        PostFactory(topic=topic, author=self.user2, position=1)
        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertEqual(response.status_code, 200)

        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_add_subscribed_tag(self):
        """
        When the topic is edited and a tag is added to which the user has subscribed
        """
        NewTopicSubscription.objects.toggle_follow(self.tag1, self.user2)

        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)

        self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
                "tags": "Linux",
            },
            follow=False,
        )

        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

    def test_remove_subscribed_tag(self):
        """
        When the topic is edited and a tag is added to which the user has subscribed
        """
        NewTopicSubscription.objects.toggle_follow(self.tag1, self.user2)

        topic = TopicFactory(forum=self.forum11, author=self.user1)
        topic.add_tags(["Linux"])
        PostFactory(topic=topic, author=self.user1, position=1)

        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein été",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
                "tags": "Windows",
            },
            follow=False,
        )

        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False, is_dead=True).all()))


@override_for_contents()
class NotificationPublishableContentTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app["member"]["bot_account"] = ProfileFactory().user.username

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

        self.client.force_login(self.user1)

    def test_follow_content_at_publication(self):
        """
        When a content is published, authors automatically follow it.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        # Signal call by the view at the publication.
        signals.content_published.send(sender=self.tuto.__class__, instance=self.tuto, by_email=False)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_follow_content_from_view(self):
        """
        Allows a user to follow (or not) a content from the view.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        result = self.client.post(reverse("content:follow-reactions", args=[self.tuto.pk]), {"follow": 1})
        self.assertEqual(result.status_code, 302)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)
        result = self.client.post(reverse("content:follow-reactions", args=[self.tuto.pk]), {"follow": 0})
        self.assertEqual(result.status_code, 302)
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertFalse(subscription.is_active)

    def test_answer_subscription(self):
        """
        When a user posts on a publishable content, the user gets subscribed.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When the notification is a reaction, it is marked as read
        when the corresponding content is displayed to the user.
        """
        ContentReactionFactory(related_content=self.tuto, author=self.user1, position=1)
        last_note = ContentReactionFactory(related_content=self.tuto, author=self.user2, position=2)
        self.tuto.last_note = last_note
        self.tuto.save()

        notification = Notification.objects.get(subscription__user=self.user1)
        self.assertFalse(notification.is_read)

        result = self.client.get(reverse("tutorial:view", args=[self.tuto.pk, self.tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__user=self.user1)
        self.assertTrue(notification.is_read)

    def test_subscription_to_new_publications_from_user(self):
        """
        Any user may subscribe to new publications from a user.
        """
        result = self.client.post(reverse("content:follow", args=[self.user1.pk]), follow=False)
        self.assertEqual(result.status_code, 403)

        self.client.logout()
        self.client.force_login(self.user2)

        result = self.client.post(
            reverse("content:follow", args=[self.user1.pk]),
            {"follow": 1},
            follow=False,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        subscription = NewPublicationSubscription.objects.get_existing(user=self.user2, content_object=self.user1)
        self.assertTrue(subscription.is_active)

        result = self.client.post(
            reverse("content:follow", args=[self.user1.pk]),
            {"email": 1},
            follow=False,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        subscription = NewPublicationSubscription.objects.get_existing(user=self.user2, content_object=self.user1)
        self.assertTrue(subscription.is_active)
        self.assertTrue(subscription.by_email)

    def test_notification_generated_when_a_tuto_is_published(self):
        """
        When a user subscribe to new publications from a user, a notification is generated when a publication is
        published.
        """
        subscription = NewPublicationSubscription.objects.toggle_follow(self.user1, self.user2)

        signals.content_published.send(sender=self.tuto.__class__, instance=self.tuto, by_email=False)

        notifications = Notification.objects.filter(subscription=subscription, is_read=False).all()
        self.assertEqual(1, len(notifications))

        signals.content_read.send(
            sender=self.tuto.__class__, instance=self.tuto, user=self.user2, target=ContentReaction
        )

        notifications = Notification.objects.filter(subscription=subscription, is_read=False).all()
        self.assertEqual(1, len(notifications))

        signals.content_read.send(
            sender=self.tuto.__class__, instance=self.tuto, user=self.user2, target=PublishableContent
        )

        notifications = Notification.objects.filter(subscription=subscription, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_no_persistant_notif_when_follow_and_quit_authorship(self):
        """
        Related to #5544. The following scenario is tested:
        1. user1 follows user2
        2. user2 publishes a content written with user3
        3. user1 gets a notification, but don't click on it
        4. user2 quits authorship of the content (but is still an author of the published version)
        5. user1 clicks on the notification, the notification should disappear
        """

        user1 = ProfileFactory().user
        user2 = ProfileFactory().user
        user3 = ProfileFactory().user

        # user1 follows user2
        self.client.logout()
        self.client.force_login(user1)
        result = self.client.post(
            reverse("content:follow", args=[user2.pk]),
            {"follow": 1},
            follow=False,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        # user2 publishes a content written with user3
        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto.authors.add(user2)
        tuto.authors.add(user3)
        UserGalleryFactory(gallery=tuto.gallery, user=user2, mode="W")
        tuto.licence = LicenceFactory()
        tuto.subcategory.add(SubCategoryFactory())
        tuto.save()
        tuto_draft = tuto.load_version()
        version = tuto_draft.current_version
        published = publish_content(tuto, tuto_draft, is_major_update=True)
        tuto.sha_public = version
        tuto.sha_draft = version
        tuto.public_version = published
        tuto.save()
        notify_update(tuto, is_update=False, is_major=True)

        # all users get a notification:
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user1).count())
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user2).count())
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user3).count())

        # user2 quits authorship of the content
        self.client.logout()
        self.client.force_login(user2)
        result = self.client.post(
            reverse("content:remove-author", args=[tuto.pk]), {"username": user2.username}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # user1 still has the notification
        notifications = Notification.objects.get_unread_notifications_of(user1)
        self.assertEqual(1, notifications.count())

        # user1 marks the notification as read by visiting the content
        self.client.logout()
        self.client.force_login(user1)
        result = self.client.get(notifications[0].url)
        self.assertEqual(result.status_code, 200)

        # the notification is read now
        self.assertEqual(0, Notification.objects.get_unread_notifications_of(user1).count())

    def test_no_persistant_notif_when_follow_and_quit_authorship_and_publish(self):
        """
        Related to #5544. Similar to
        test_no_persistant_notif_when_follow_and_quit_authorship, but this time
        the content is published. The following scenario is tested:
        1. user1 follows user2
        2. user2 publishes a content written with user3
        3. user1 gets a notification, but don't click on it
        4. user2 quits authorship of the content
        5. user3 publishes the content
        6. user1 clicks on the notification, the notification should disappear
        """

        user1 = ProfileFactory().user
        user2 = ProfileFactory().user
        user3 = ProfileFactory().user

        # user1 follows user2
        self.client.logout()
        self.client.force_login(user1)
        result = self.client.post(
            reverse("content:follow", args=[user2.pk]),
            {"follow": 1},
            follow=False,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        # user2 publishes a content written with user3
        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto.authors.add(user2)
        tuto.authors.add(user3)
        UserGalleryFactory(gallery=tuto.gallery, user=user2, mode="W")
        tuto.licence = LicenceFactory()
        tuto.subcategory.add(SubCategoryFactory())
        tuto.save()
        tuto_draft = tuto.load_version()
        version = tuto_draft.current_version
        published = publish_content(tuto, tuto_draft, is_major_update=True)
        tuto.sha_public = version
        tuto.sha_draft = version
        tuto.public_version = published
        tuto.save()
        notify_update(tuto, is_update=False, is_major=True)

        # all users get a notification:
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user1).count())
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user2).count())
        self.assertEqual(1, Notification.objects.get_unread_notifications_of(user3).count())

        # user2 quits authorship of the content
        self.client.logout()
        self.client.force_login(user2)
        result = self.client.post(
            reverse("content:remove-author", args=[tuto.pk]), {"username": user2.username}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # user3 publishes the content
        tuto_draft = tuto.load_version()
        version = tuto_draft.current_version
        published = publish_content(tuto, tuto_draft, is_major_update=True)
        tuto.sha_public = version
        tuto.sha_draft = version
        tuto.public_version = published
        tuto.save()
        notify_update(tuto, is_update=False, is_major=True)

        # user1 still has the notification
        notifications = Notification.objects.get_unread_notifications_of(user1)
        self.assertEqual(1, notifications.count())

        # user1 marks the notification as read by visiting the content
        self.client.logout()
        self.client.force_login(user1)
        result = self.client.get(notifications[0].url)
        self.assertEqual(result.status_code, 200)

        # the notification is read now
        self.assertEqual(0, Notification.objects.get_unread_notifications_of(user1).count())

    def test_no_error_on_multiple_subscription(self):
        subscription = NewPublicationSubscription.objects.toggle_follow(self.user1, self.user2)

        signals.content_published.send(sender=self.tuto.__class__, instance=self.tuto, by_email=False)

        subscription1 = Notification.objects.filter(subscription=subscription, is_read=False).first()
        subscription2 = copy.copy(subscription1)
        subscription2.save()
        subscription.mark_notification_read(self.tuto)
        subscription1 = Notification.objects.filter(subscription=subscription, is_read=False).first()
        self.assertIsNone(subscription1)
        self.assertEqual(1, Notification.objects.filter(subscription=subscription, is_read=True).count())


class NotificationPrivateTopicTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.user3 = ProfileFactory().user
        self.user1.profile.email_for_new_mp = True
        self.user2.profile.email_for_new_mp = True
        self.user3.profile.email_for_new_mp = False
        self.user1.profile.save()
        self.user2.profile.save()
        self.user3.profile.save()

        self.client.force_login(self.user1)

    def test_creation_private_topic(self):
        """
        When we create a topic, its author follows it.
        """
        topic = send_mp(author=self.user1, users=[], title="Testing", subtitle="", text="", leave=False)

        subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(topic)
        self.assertEqual(1, len(subscriptions))
        self.assertEqual(self.user1, subscriptions[0].user)
        self.assertTrue(subscriptions[0].by_email)
        self.assertIsNone(subscriptions[0].last_notification)

    def test_generate_a_notification_for_all_participants(self):
        """
        When we create a topic, all participants have a notification for the last message.
        """
        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user2)
        self.assertEqual(0, len(subscriptions))

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(0, len(subscriptions))

        topic = send_mp(
            author=self.user1, users=[self.user2, self.user3], title="Testing", subtitle="", text="", leave=False
        )

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user2)
        self.assertEqual(1, len(subscriptions))
        self.assertEqual(topic, subscriptions.first().content_object)

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(1, len(subscriptions))
        self.assertEqual(topic, subscriptions.first().content_object)

        notification = Notification.objects.get_unread_notifications_of(self.user2).first()
        self.assertIsNotNone(notification)
        self.assertEqual(topic.last_message, notification.content_object)

        notification = Notification.objects.get_unread_notifications_of(self.user3).first()
        self.assertIsNotNone(notification)
        self.assertEqual(topic.last_message, notification.content_object)

    def test_mark_read_a_notification(self):
        """
        When we mark a private topic as read, we mark its notification as read.
        """
        topic = send_mp(
            author=self.user1, users=[self.user2, self.user3], title="Testing", subtitle="", text="", leave=False
        )

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        mark_read(topic, self.user2)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(0, len(notifications))

    def test_generate_a_notification_after_new_post(self):
        """
        When a user posts on a private topic, we generate a notification for all participants.
        """
        topic = send_mp(
            author=self.user1, users=[self.user2, self.user3], title="Testing", subtitle="", text="", leave=False
        )

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        mark_read(topic, self.user2)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(0, len(notifications))

        send_message_mp(self.user3, topic, "")

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

    def test_generate_a_notification_when_add_a_participant(self):
        """
        When we add a user to a private topic, we generate a notification for this user
        at the last message.
        """
        topic = send_mp(author=self.user1, users=[self.user2], title="Testing", subtitle="", text="", leave=False)

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(0, len(subscriptions))

        topic.add_participant(self.user3)
        topic.save()

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(1, len(subscriptions))

        notifications = Notification.objects.get_unread_notifications_of(self.user3)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.filter())
        self.assertEqual(topic.last_message, notifications.first().content_object)

    def test_remove_notifications_when_a_user_leave_private_topic(self):
        """
        When a user leaves a private topic, we mark the current notification as read
        if it exists.
        """
        topic = send_mp(author=self.user1, users=[self.user2], title="Testing", subtitle="", text="", leave=False)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        self.assertIsNotNone(PrivateTopicAnswerSubscription.objects.get_existing(self.user2, topic, is_active=True))

        send_message_mp(self.user2, topic, "Test")
        topic.remove_participant(self.user2)
        topic.save()

        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user2)))
        self.assertIsNotNone(PrivateTopicAnswerSubscription.objects.get_existing(self.user2, topic, is_active=False))

        self.assertEqual(1, len(Notification.objects.get_unread_notifications_of(self.user1)))

        response = self.client.post(reverse("mp:leave", args=[topic.pk, topic.slug()]), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user1)))

    def test_send_an_email_when_we_specify_it(self):
        """
        When the user asked to be notified via email, we actually send the email
        when a topic is created.
        """
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.assertEqual(0, len(mail.outbox))

        topic = send_mp(
            author=self.user1,
            users=[self.user2, self.user3],
            title="Testing",
            subtitle="",
            text="",
            send_by_mail=True,
            leave=False,
        )

        self.assertEqual(1, len(mail.outbox))

        self.user1.profile.email_for_answer = True
        self.user1.profile.save()
        self.user2.profile.email_for_answer = True
        self.user2.profile.save()
        self.user3.profile.email_for_answer = False
        self.user3.profile.save()

        send_message_mp(self.user2, topic, "", send_by_mail=True)
        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user2)
        self.assertTrue(subscriptions.last().by_email)

        self.assertEqual(2, len(mail.outbox))

        self.user1.profile.email_for_answer = False
        self.user1.profile.save()

        send_message_mp(self.user2, topic, "", send_by_mail=True)

        self.assertEqual(2, len(mail.outbox))


class NotificationTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        self.client.force_login(self.user1)

    def test_reuse_old_notification(self):
        """
        When there already is a read notification for a given content, we reuse it.
        """
        topic = send_mp(author=self.user1, users=[self.user2], title="Testing", subtitle="", text="", leave=False)
        send_message_mp(self.user2, topic, "", send_by_mail=True)

        notifications = Notification.objects.get_unread_notifications_of(self.user1)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        mark_read(topic, self.user1)

        send_message_mp(self.user2, topic, "", send_by_mail=True)

        notifications = Notification.objects.filter(subscription__user=self.user1)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())

    def test_mark_all_notifications_as_read_when_toggle_follow(self):
        """
        When a user unsubscribes from a content, we mark all notifications for
        this content as read.
        """
        category = ForumCategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        PostFactory(topic=topic, author=self.user2, position=2)

        notifications = Notification.objects.get_unread_notifications_of(self.user1)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        TopicAnswerSubscription.objects.toggle_follow(topic, self.user1)

        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user1)))

    def test_no_duplicate_subscription(self):
        """
        Creating two same subscriptions is rejected by the database.
        """
        category = ForumCategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=self.user1)
        TopicAnswerSubscription.objects.toggle_follow(topic, self.user1, True)

        subscription = TopicAnswerSubscription(user=self.user1, content_object=topic)
        with self.assertRaises(IntegrityError):
            subscription.save()

    def test_new_cowritten_content_without_doubly_notif(self):
        author1 = ProfileFactory()
        author2 = ProfileFactory()
        NewPublicationSubscription.objects.toggle_follow(author2.user, author1.user)
        content = PublishedContentFactory(author_list=[author1.user, author2.user])
        signals.content_published.send(sender=content.__class__, instance=content, by_email=False)
        auto_user_1_sub = NewPublicationSubscription.objects.get_existing(author1.user, author1.user, False)
        self.assertIsNotNone(auto_user_1_sub)
        notifs = list(Notification.objects.get_notifications_of(author1.user))
        self.assertEqual(1, len(notifs))

    def test_mark_notifications_as_read(self):
        category = ForumCategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        PostFactory(topic=topic, author=self.user2, position=2)

        self.client.force_login(self.user1)

        notifications = Notification.objects.get_unread_notifications_of(self.user1)
        self.assertEqual(1, len(notifications))

        self.assertFalse(topic.is_read)

        result = self.client.post(reverse("notification:mark-as-read"), follow=False)
        self.assertEqual(result.status_code, 302)

        notifications = Notification.objects.get_unread_notifications_of(self.user1)
        self.assertEqual(0, len(notifications))

        self.assertTrue(Topic.objects.get(pk=topic.pk).is_read)
