from django.test import TestCase
from django.core.urlresolvers import reverse

from zds.forum.factories import CategoryFactory, ForumFactory
from zds.forum.models import Topic
from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.notification.models import NewTopicSubscription


class ForumNotification(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.assertTrue(self.staff.has_perm("forum.change_topic"))
        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)
        for group in self.staff.groups.all():
            self.forum12.group.add(group)
        self.forum12.save()

    def test_no_dead_notif_on_moving(self):
        NewTopicSubscription.objects.get_or_create_active(self.user1, self.forum11)
        self.assertTrue(self.client.login(username=self.user2.username, password='hostel77'))
        result = self.client.post(
            reverse('topic-new') + '?forum={0}'.format(self.forum11.pk),
            {
                'title': u'Super sujet',
                'subtitle': u'Pour tester les notifs',
                'text': u'En tout cas l\'un abonnement',
                'tags': ''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title=u'Super sujet').first()
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, "There must be an active subscription for now")
        self.assertIsNotNone(subscription.last_notification, "There must be a notification for now")
        self.assertFalse(subscription.last_notification.is_read)
        self.client.logout()
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))
        data = {
            'move': '',
            'forum': self.forum12.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)
        self.assertEqual(302, response.status_code)
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, "There must still be an active subscription")
        self.assertIsNotNone(subscription.last_notification,
                             "There must still be a notification as object is not removed.")
        self.assertTrue(subscription.last_notification.is_read, "As forum is not reachable, notification is read")
