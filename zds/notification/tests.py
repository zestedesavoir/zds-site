# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds import settings
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import mark_read
from zds.notification import signals
from zds.notification.models import Notification, TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    PrivateTopicAnswerSubscription, NewTopicSubscription
from zds.tutorialv2.factories import PublishableContentFactory, LicenceFactory, ContentReactionFactory, \
    SubCategoryFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.utils import slugify
from zds.utils.mps import send_mp, send_message_mp


class NotificationForumTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)

        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))

    def test_creation_topic(self):
        """
        When we create a topic, the author follow it.
        """
        result = self.client.post(
            reverse('topic-new') + '?forum={0}'.format(self.forum12.pk),
            {
                'title': u'Super sujet',
                'subtitle': u'Pour tester les notifs',
                'text': u'En tout cas l\'un abonnement'
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title=u'Super sujet').first()
        content_type = ContentType.objects.get_for_model(topic)

        subscription = TopicAnswerSubscription.objects.get(object_id=topic.pk,
                                                           content_type__pk=content_type.pk,
                                                           user=self.user1)
        self.assertEqual(subscription.is_active, True)

    def test_mark_read_a_topic_from_view_list_posts(self):
        """
        Check that we can subscribe to a topic, we generate a new notification when
        another user post a message and if we display list of messages, the notification
        is marked as read.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)

        # Follow the topic.
        self.assertIsNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic))
        subscription = TopicAnswerSubscription.objects.get_or_create_active(self.user1, topic)

        # Creates a new post in the topic to generate a new notification.
        PostFactory(topic=topic, author=self.user2, position=1)
        content_notification_type = ContentType.objects.get_for_model(topic.last_message)
        notification = Notification.objects.get(subscription=subscription,
                                                content_type__pk=content_notification_type.pk,
                                                object_id=topic.last_message.pk, is_read=False)
        self.assertIsNotNone(notification)

        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))
        self.assertEqual(response.status_code, 200)

        # Checks that the notification is reading now.
        notification = Notification.objects.get(subscription=subscription,
                                                content_type__pk=content_notification_type.pk,
                                                object_id=topic.last_message.pk, is_read=True)
        self.assertIsNotNone(notification)

    def test_answer_topic(self):
        """
        When a user post on a topic, a subscription to the topic concerned is created
        for this user.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)

        result = self.client.post(
            reverse('post-new') + '?sujet={0}'.format(topic1.pk),
            {
                'last_post': topic1.last_message.pk,
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 302)

        # check that topic creator has been notified
        notification = Notification.objects.get(subscription__user=self.user2)
        subscription_content_type = ContentType.objects.get_for_model(topic1)

        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.subscription.content_type, subscription_content_type)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

        # check that answerer has subscribed to the topic
        subscription = TopicAnswerSubscription.objects.get(object_id=topic1.pk,
                                                           content_type__pk=subscription_content_type.pk,
                                                           user=self.user1)
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When we post on a topic, a notification is created for each subscribers. We can
        read a notification when we display list of messages of the topic concerned.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)

        result = self.client.post(
            reverse('post-new') + '?sujet={0}'.format(topic1.pk),
            {
                'last_post': topic1.last_message.pk,
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__user=self.user2)
        self.assertEqual(notification.is_read, False)

        self.client.logout()
        self.assertTrue(self.client.login(username=self.user2.username, password='hostel77'), True)

        result = self.client.get(reverse('topic-posts-list', args=[topic1.pk, slugify(topic1.title)]), follow=True)
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__user=self.user2)
        self.assertEqual(notification.is_read, True)

    def test_subscription_deactivated_and_notification_read_when_topic_moved(self):
        """
        When a topic is moved in a forum where subscribers can't read it, the subscription
        should be deactivated and notifications read.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        PostFactory(topic=topic, author=ProfileFactory().user, position=2)

        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic, is_active=True))
        self.assertIsNotNone(Notification.objects.get(subscription__user=self.user1, is_read=False))

        forum_not_read = ForumFactory(category=self.category1, position_in_category=2)
        forum_not_read.group.add(Group.objects.create(name="DummyGroup_1"))

        self.assertTrue(self.client.login(username=StaffProfileFactory().user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': forum_not_read.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.user1, topic, is_active=False))
        self.assertIsNotNone(Notification.objects.get(subscription__user=self.user1, is_read=True))

    def test_post_unread(self):
        """
        When a post is marked unread, a notification is generated.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)
        PostFactory(topic=topic1, author=self.user1, position=2)
        post = PostFactory(topic=topic1, author=self.user2, position=3)

        result = self.client.get(reverse('post-unread') + '?message={}'.format(post.pk), follow=False)

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__user=self.user1, object_id=post.pk, is_read=False)
        self.assertEqual(notification.object_id, post.pk)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

    def test_hide_post_mark_notification_as_read(self):
        """
        Check if notification is deleted if post is hide.
        """
        topic = TopicFactory(forum=self.forum11, author=self.user1)
        PostFactory(topic=topic, author=self.user1, position=1)
        PostFactory(topic=topic, author=self.user2, position=2)
        PostFactory(topic=topic, author=ProfileFactory().user, position=3)

        notifications = Notification.objects.filter(object_id=topic.last_message.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        # hide last post
        data = {
            'delete_message': ''
        }
        self.assertTrue(self.client.login(username=StaffProfileFactory().user.username, password='hostel77'))
        response = self.client.post(
            reverse('post-edit') + '?message={}'.format(topic.last_message.pk), data, follow=False)
        self.assertEqual(302, response.status_code)

        notifications = Notification.objects.filter(object_id=topic.last_message.pk, is_read=True).all()
        self.assertEqual(1, len(notifications))

    def test_topics_followed_by_a_user(self):
        """
        Check that we retrieve well topics followed by a user.
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
        When a user subscribes to a forum, he receive a notification for each topic created.
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
        When a user have a notification on a topic, the notification should be marked as read.
        """
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(1, len(notifications))

        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))
        self.assertEqual(response.status_code, 200)

        notifications = Notification.objects.filter(object_id=topic.pk, is_read=False).all()
        self.assertEqual(0, len(notifications))

    def test_move_topic_from_forum_to_another_one(self):
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False).all()))

        # Move the topic in another forum.
        self.client.logout()
        staff = StaffProfileFactory()
        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': self.forum12.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)
        self.assertEqual(302, response.status_code)

        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(self.forum12, topic.forum)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False, is_dead=True).all()))

        self.client.logout()
        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))
        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=True, is_dead=True).all()))

    def test_move_topic_from_forum_followed_to_forum_followed_too(self):
        NewTopicSubscription.objects.toggle_follow(self.forum11, self.user1)
        NewTopicSubscription.objects.toggle_follow(self.forum12, self.user1)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False).all()))

        # Move the topic in another forum.
        self.client.logout()
        staff = StaffProfileFactory()
        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': self.forum12.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)
        self.assertEqual(302, response.status_code)

        topic = Topic.objects.get(pk=topic.pk)
        self.assertEqual(self.forum12, topic.forum)
        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=False, is_dead=False).all()))

        self.client.logout()
        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))
        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(Notification.objects.filter(object_id=topic.pk, is_read=True, is_dead=False).all()))


class NotificationPublishableContentTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user1)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user1, mode='W')
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

        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))

    def test_follow_content_at_publication(self):
        """
        When a content is published, authors follow it.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        # Signal call by the view at the publication.
        signals.new_content.send(sender=self.tuto.__class__, instance=self.tuto, by_email=False)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_follow_content_from_view(self):
        """
        Allows a user to follow (or not), a content from the view.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        result = self.client.post(reverse('content:follow', args=[self.tuto.pk]), {'follow': 1})
        self.assertEqual(result.status_code, 302)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_answer_subscription(self):
        """
        When a user post on a publishable content, a subscription is created for this user.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertIsNone(subscription)

        result = self.client.post(reverse("content:add-reaction") + u'?pk={}'.format(self.tuto.pk), {
            'text': u'message',
            'last_note': '0'
        }, follow=True)
        self.assertEqual(result.status_code, 200)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(user=self.user1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When we have a notification a reaction, this notification is marked as read
        when we display it at the user.
        """
        ContentReactionFactory(related_content=self.tuto, author=self.user1, position=1)
        last_note = ContentReactionFactory(related_content=self.tuto, author=self.user2, position=2)
        self.tuto.last_note = last_note
        self.tuto.save()

        notification = Notification.objects.get(subscription__user=self.user1)
        self.assertFalse(notification.is_read)

        result = self.client.get(reverse('tutorial:view', args=[self.tuto.pk, self.tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__user=self.user1)
        self.assertTrue(notification.is_read)


class NotificationPrivateTopicTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.user3 = ProfileFactory().user

        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))

    def test_creation_private_topic(self):
        """
        When we create a topic, the author follow it.
        """
        topic = send_mp(author=self.user1, users=[], title="Testing", subtitle="", text="", leave=False)

        subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(topic)
        self.assertEqual(1, len(subscriptions))
        self.assertEqual(self.user1, subscriptions[0].user)
        self.assertTrue(subscriptions[0].by_email)
        self.assertIsNone(subscriptions[0].last_notification)

    def test_generate_a_notification_for_all_participants(self):
        """
        When we create a topic, all participants have a notification to the last message.
        """
        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user2)
        self.assertEqual(0, len(subscriptions))

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(0, len(subscriptions))

        topic = send_mp(author=self.user1,
                        users=[self.user2, self.user3],
                        title="Testing", subtitle="", text="", leave=False)

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
        When we mark as read a private topic, we mark as read its notification.
        """
        topic = send_mp(author=self.user1,
                        users=[self.user2, self.user3],
                        title="Testing", subtitle="", text="", leave=False)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        mark_read(topic, self.user2)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(0, len(notifications))

    def test_generate_a_notification_after_new_post(self):
        """
        When a user post on a private topic, we generate a notification for all participants.
        """
        topic = send_mp(author=self.user1,
                        users=[self.user2, self.user3],
                        title="Testing", subtitle="", text="", leave=False)

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
        When we add a user in a private topic, we generate a notification for this user at the last message.
        """
        topic = send_mp(author=self.user1,
                        users=[self.user2],
                        title="Testing", subtitle="", text="", leave=False)

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(0, len(subscriptions))

        topic.participants.add(self.user3)
        topic.save()

        subscriptions = PrivateTopicAnswerSubscription.objects.filter(user=self.user3)
        self.assertEqual(1, len(subscriptions))

        notifications = Notification.objects.get_unread_notifications_of(self.user3)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.filter())
        self.assertEqual(topic.last_message, notifications.first().content_object)

    def test_remove_notifications_when_a_user_leave_private_topic(self):
        """
        When a user leave a private topic, we mark read the current notification if exist.
        """
        topic = send_mp(author=self.user1,
                        users=[self.user2],
                        title="Testing", subtitle="", text="", leave=False)

        notifications = Notification.objects.get_unread_notifications_of(self.user2)
        self.assertEqual(1, len(notifications))
        self.assertIsNotNone(notifications.first())
        self.assertEqual(topic.last_message, notifications.first().content_object)

        self.assertIsNotNone(PrivateTopicAnswerSubscription.objects.get_existing(self.user2, topic, is_active=True))

        send_message_mp(self.user2, topic, "Test")
        topic.participants.remove(self.user2)
        topic.save()

        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user2)))
        self.assertIsNotNone(PrivateTopicAnswerSubscription.objects.get_existing(self.user2, topic, is_active=False))

        self.assertEqual(1, len(Notification.objects.get_unread_notifications_of(self.user1)))

        response = self.client.post(reverse('mp-delete', args=[topic.pk, topic.slug]), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user1)))

    def test_send_an_email_when_we_specify_it(self):
        """
        When we ask at the back-end than we want send an email at the creation of a topic, we send it.
        """
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.assertEquals(0, len(mail.outbox))

        topic = send_mp(author=self.user1, users=[self.user2],
                        title="Testing", subtitle="", text="",
                        send_by_mail=True, leave=False)

        self.assertEquals(1, len(mail.outbox))

        self.user1.profile.email_for_answer = True
        self.user1.profile.save()

        send_message_mp(self.user2, topic, "", send_by_mail=True)

        self.assertEquals(2, len(mail.outbox))

        self.user1.profile.email_for_answer = False
        self.user1.profile.save()

        send_message_mp(self.user2, topic, "", send_by_mail=True)

        self.assertEquals(2, len(mail.outbox))


class NotificationTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))

    def test_reuse_old_notification(self):
        """
        When there is already a notification marked read for a given content, we reuse it.
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
        When a user unsubscribe to a content, we mark as read all notifications about this content.
        """
        category = CategoryFactory(position=1)
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
