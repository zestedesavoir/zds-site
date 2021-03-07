import datetime
from django.test import TestCase
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory
from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Alert
from zds.utils.context_processor import get_header_notifications
from zds.utils.templatetags.topics_sort import topics_sort
from zds.forum.factories import TopicFactory, create_category_and_forum, create_topic_in_forum


class Misc(TestCase):
    def test_utf8mb4(self):
        self.assertFalse(contains_utf8mb4("abc"))
        self.assertFalse(contains_utf8mb4("abc"))
        self.assertFalse(contains_utf8mb4("abc€"))
        self.assertFalse(contains_utf8mb4("abc€"))
        self.assertTrue(contains_utf8mb4("a🐙tbc€"))
        self.assertTrue(contains_utf8mb4("a🐙tbc€"))

    def test_intervention_filter_for_tribunes(self):
        author = ProfileFactory()
        opinion = PublishedContentFactory(type="OPINION", author_list=[author.user])
        alerter = ProfileFactory()
        staff = StaffProfileFactory()
        alert = Alert()
        alert.scope = "CONTENT"
        alert.author = alerter.user
        alert.content = opinion
        alert.pubdate = datetime.datetime.now()
        alert.text = "Something to say."
        alert.save()
        filter_result = get_header_notifications(staff.user)["alerts"]
        self.assertEqual(1, filter_result["total"])
        self.assertEqual(alert.text, filter_result["list"][0]["text"])

    def test_topics_sort(self):
        author = ProfileFactory()
        _, forum = create_category_and_forum()
        topic1 = create_topic_in_forum(forum, author)
        topic2 = create_topic_in_forum(forum, author)

        self.assertEqual(topics_sort([topic1, topic2]), [topic2, topic1])
