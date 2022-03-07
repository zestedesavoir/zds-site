from datetime import datetime, timedelta

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.utils.context_processor import header_notifications as notifications_processor
from zds.utils.models import Alert


class AlertsTest(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory()
        self.dummy_author = ProfileFactory()

        self.category = ForumCategoryFactory(position=1)
        self.forum = ForumFactory(category=self.category, position_in_category=1)
        self.topic = TopicFactory(forum=self.forum, author=self.dummy_author.user)
        self.post = PostFactory(topic=self.topic, author=self.dummy_author.user, position=1)

        self.alerts = []
        for i in range(20):
            alert = Alert(
                author=self.dummy_author.user,
                comment=self.post,
                scope="FORUM",
                text=f"pouet-{i}",
                pubdate=(datetime.now() + timedelta(minutes=i)),
            )
            alert.save()
            self.alerts.append(alert)

    def test_anonymous_user(self):
        self.assertEqual({}, AlertsTest.__notifications(AnonymousUser()))

    def test_regular_user(self):
        self.assertEqual(False, AlertsTest.__alerts(self.dummy_author.user))

    def test_staff(self):
        alerts = AlertsTest.__alerts(self.staff.user)
        self.assertEqual(20, alerts["total"])
        self.assertEqual(10, len(alerts["list"]))
        self.assertEqual(self.alerts[-1].text, alerts["list"][0]["text"])

        self.alerts[5].delete()
        alerts = AlertsTest.__alerts(self.staff.user)
        self.assertEqual(19, alerts["total"])
        self.assertEqual(10, len(alerts["list"]))

    @staticmethod
    def __alerts(user):
        return AlertsTest.__notifications(user)["header_alerts"]

    @staticmethod
    def __notifications(user):
        class Request:
            pass

        r = Request()
        r.user = user
        return notifications_processor(r)
