# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.notification.models import Notification, TopicAnswerSubscription, ContentReactionAnswerSubscription
from zds.tutorialv2.factories import PublishableContentFactory, LicenceFactory, SubCategoryFactory, \
    ContentReactionFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.utils import slugify


class NotificationForumTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)

        self.assertTrue(self.client.login(username=self.profile1.user.username, password='hostel77'))

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
                                                           profile=self.profile1)
        self.assertEqual(subscription.is_active, True)

    def test_mark_read_a_topic_from_view_list_posts(self):
        """
        Check that we can subscribe to a topic, we generate a new notification when
        another user post a message and if we display list of messages, the notification
        is marked as read.
        """
        topic = TopicFactory(forum=self.forum11, author=self.profile2.user)
        PostFactory(topic=topic, author=self.profile2.user, position=1)

        # Follow the topic.
        self.assertIsNone(TopicAnswerSubscription.objects.get_existing(self.profile1, topic))
        subscription = TopicAnswerSubscription.objects.get_or_create_active(self.profile1, topic)

        # Creates a new post in the topic to generate a new notification.
        PostFactory(topic=topic, author=self.profile2.user, position=1)
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
        topic1 = TopicFactory(forum=self.forum11, author=self.profile2.user)
        PostFactory(topic=topic1, author=self.profile2.user, position=1)

        result = self.client.post(
            reverse('post-new') + '?sujet={0}'.format(topic1.pk),
            {
                'last_post': topic1.last_message.pk,
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 302)

        # check that topic creator has been notified
        notification = Notification.objects.get(subscription__profile=self.profile2)
        subscription_content_type = ContentType.objects.get_for_model(topic1)

        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.subscription.content_type, subscription_content_type)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

        # check that answerer has subscribed to the topic
        subscription = TopicAnswerSubscription.objects.get(object_id=topic1.pk,
                                                           content_type__pk=subscription_content_type.pk,
                                                           profile=self.profile1)
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When we post on a topic, a notification is created for each subscribers. We can
        read a notification when we display list of messages of the topic concerned.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.profile2.user)
        PostFactory(topic=topic1, author=self.profile2.user, position=1)

        result = self.client.post(
            reverse('post-new') + '?sujet={0}'.format(topic1.pk),
            {
                'last_post': topic1.last_message.pk,
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__profile=self.profile2)
        self.assertEqual(notification.is_read, False)

        self.client.logout()
        self.assertTrue(self.client.login(username=self.profile2.user.username, password='hostel77'), True)

        result = self.client.get(reverse('topic-posts-list', args=[topic1.pk, slugify(topic1.title)]), follow=True)
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__profile=self.profile2)
        self.assertEqual(notification.is_read, True)

    def test_subscription_deactivated_and_notification_read_when_topic_moved(self):
        """
        When a topic is moved in a forum where subscribers can't read it, the subscription
        should be deactivated and notifications read.
        """
        topic = TopicFactory(forum=self.forum11, author=self.profile1.user)
        PostFactory(topic=topic, author=self.profile1.user, position=1)
        PostFactory(topic=topic, author=ProfileFactory().user, position=2)

        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.profile1, topic, is_active=True))
        self.assertIsNotNone(Notification.objects.get(subscription__profile=self.profile1, is_read=False))

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
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.profile1, topic, is_active=False))
        self.assertIsNotNone(Notification.objects.get(subscription__profile=self.profile1, is_read=True))

    def test_post_unread(self):
        """
        When a post is marked unread, a notification is generated.
        """
        topic1 = TopicFactory(forum=self.forum11, author=self.profile2.user)
        PostFactory(topic=topic1, author=self.profile2.user, position=1)
        PostFactory(topic=topic1, author=self.profile1.user, position=2)
        post = PostFactory(topic=topic1, author=self.profile2.user, position=3)

        result = self.client.get(reverse('post-unread') + '?message={}'.format(post.pk), follow=False)

        self.assertEqual(result.status_code, 302)

        notification = Notification.objects.get(subscription__profile=self.profile1, object_id=post.pk, is_read=False)
        self.assertEqual(notification.object_id, post.pk)
        self.assertEqual(notification.subscription.object_id, topic1.pk)

    def test_hide_post_mark_notification_as_read(self):
        """
        Check if notification is deleted if post is hide.
        """
        topic = TopicFactory(forum=self.forum11, author=self.profile1.user)
        PostFactory(topic=topic, author=self.profile1.user, position=1)
        PostFactory(topic=topic, author=self.profile2.user, position=2)
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


class NotificationPublishableContentTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        # create a tutorial
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.profile1.user)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.profile1.user, mode='W')
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

        self.assertTrue(self.client.login(username=self.profile1.user.username, password='hostel77'))

    def test_answer_subscription(self):
        """
        When a user post on a publishable content, a subscription is created for this user.
        """
        subscription = ContentReactionAnswerSubscription.objects.get_existing(
            profile=self.profile1, content_object=self.tuto)
        self.assertIsNone(subscription)

        result = self.client.post(reverse("content:add-reaction") + u'?pk={}'.format(self.tuto.pk), {
            'text': u'message',
            'last_note': '0'
        }, follow=True)
        self.assertEqual(result.status_code, 200)

        subscription = ContentReactionAnswerSubscription.objects.get_existing(
            profile=self.profile1, content_object=self.tuto)
        self.assertTrue(subscription.is_active)

    def test_notification_read(self):
        """
        When we have a notification a reaction, this notification is marked as read
        when we display it at the user.
        """
        ContentReactionFactory(related_content=self.tuto, author=self.profile1.user, position=1)
        last_note = ContentReactionFactory(related_content=self.tuto, author=self.profile2.user, position=2)
        self.tuto.last_note = last_note
        self.tuto.save()

        notification = Notification.objects.get(subscription__profile=self.profile1)
        self.assertFalse(notification.is_read)

        result = self.client.get(reverse('tutorial:view', args=[self.tuto.pk, self.tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        notification = Notification.objects.get(subscription__profile=self.profile1)
        self.assertTrue(notification.is_read)
