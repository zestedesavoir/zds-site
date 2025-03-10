from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from zds.forum.feeds import LastPostsFeedATOM, LastPostsFeedRSS, LastTopicsFeedATOM, LastTopicsFeedRSS
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TagFactory, TopicFactory
from zds.member.tests.factories import ProfileFactory


class LastTopicsFeedTest(TestCase):
    def setUp(self):
        # prepare a user and 2 Topic (with and without tags)

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        self.category1 = ForumCategoryFactory(position=1)
        self.forum = ForumFactory(category=self.category1, position_in_category=1)
        self.forum2 = ForumFactory(category=self.category1, position_in_category=2)

        self.user = ProfileFactory().user
        self.client.force_login(self.user)

        self.tag = TagFactory()
        self.topic1 = TopicFactory(forum=self.forum, author=self.user)
        self.topic2 = TopicFactory(forum=self.forum2, author=self.user)
        self.topic2.tags.add(self.tag)
        self.topic2.save()

        self.topicfeed = LastTopicsFeedRSS()

    def test_is_well_setup(self):
        """Test that base parameters are Ok"""

        self.assertEqual(self.topicfeed.link, "/forums/")
        reftitle = "Derniers sujets sur {}".format(settings.ZDS_APP["site"]["literal_name"])
        self.assertEqual(self.topicfeed.title, reftitle)
        refdescription = "Les derniers sujets créés sur le forum de {}.".format(
            settings.ZDS_APP["site"]["literal_name"]
        )
        self.assertEqual(self.topicfeed.description, refdescription)

        atom = LastTopicsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_getobjects(self):
        """Get object should return the given parameteres in an object"""

        factory = RequestFactory()
        request = factory.get(reverse("forum:topic-feed-rss") + "?forum=fofo&tag=tatag")
        obj = self.topicfeed.get_object(request=request)
        self.assertEqual(obj["forum"], "fofo")
        self.assertEqual(obj["tag"], "tatag")

    def test_items_success(self):
        """test that right items are sent back according to obj"""

        # test empty obj
        obj = {}
        # should return all topics
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 2)
        # test with a tag
        obj = {"tag": self.tag.pk}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 1)
        # test with a forum
        obj = {"forum": self.topic1.forum.pk}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 1)
        # test with a forum and a tag
        obj = {"forum": self.topic1.forum.pk, "tag": self.tag.pk}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)

    def test_items_bad_cases(self):
        """test that right items are sent back according to obj"""

        # test empty values, return value should be empty
        obj = {"forum": -1, "tag": -1}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        obj = {"forum": -1}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        obj = {"tag": -1}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        # with a weird object
        obj = {"forum": "lol"}
        topics = self.topicfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)

    def test_get_pubdate(self):
        """test the return value of pubdate"""

        ref = self.topic2.pubdate
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_pubdate(item=topics[0])
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """test the return value of title"""

        ref = f"{self.topic2.title} dans {self.topic2.forum.title}"
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_title(item=topics[0])
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """test the return value of description"""

        ref = self.topic2.subtitle
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_description(item=topics[0])
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """test the return value of author name"""

        ref = self.topic2.author.username
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_author_name(item=topics[0])
        self.assertEqual(ret, ref)

    def test_get_author_link(self):
        """test the return value of author link"""

        ref = self.topic2.author.get_absolute_url()
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_author_link(item=topics[0])
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """test the return value of item link"""

        ref = self.topic2.get_absolute_url()
        topics = self.topicfeed.items(obj={"tag": self.tag.pk})
        ret = self.topicfeed.item_link(item=topics[0])
        self.assertEqual(ret, ref)

    def test_content_control_chars(self):
        """
        Test 'control characters' in content of the feed doesn't break it.

        The '\u0007' character in the post content belongs to a character
        family that is  not supported in RSS or Atom feeds and will break their
        generation.
        """
        buggy_topic = TopicFactory(forum=self.forum2, author=self.user)
        buggy_topic.title = "Strange char: \u0007"
        buggy_topic.save()

        request = self.client.get(reverse("forum:topic-feed-rss"))
        self.assertEqual(request.status_code, 200)

        request = self.client.get(reverse("forum:topic-feed-atom"))
        self.assertEqual(request.status_code, 200)


class LastPostsFeedTest(TestCase):
    def setUp(self):
        # prepare a user and 2 Topic (with and without tags)

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        self.category1 = ForumCategoryFactory(position=1)
        self.forum = ForumFactory(category=self.category1, position_in_category=1)
        self.forum2 = ForumFactory(category=self.category1, position_in_category=2)
        self.forum3 = ForumFactory(category=self.category1, position_in_category=3)

        self.user = ProfileFactory().user
        self.client.force_login(self.user)

        self.tag = TagFactory()
        self.topic1 = TopicFactory(forum=self.forum, author=self.user)
        self.topic2 = TopicFactory(forum=self.forum2, author=self.user)
        self.topic2.tags.add(self.tag)
        self.topic2.save()

        # create 2 posts in each forum
        PostFactory(topic=self.topic1, author=self.user, position=1)
        PostFactory(topic=self.topic1, author=self.user, position=2)
        PostFactory(topic=self.topic2, author=self.user, position=1)
        PostFactory(topic=self.topic2, author=self.user, position=2)

        # and last topic + post alone
        self.tag2 = TagFactory()
        self.topic3 = TopicFactory(forum=self.forum3, author=self.user)
        self.post3 = PostFactory(topic=self.topic3, author=self.user, position=1)
        self.topic3.tags.add(self.tag2)
        self.topic3.save()

        self.postfeed = LastPostsFeedRSS()

    def test_is_well_setup(self):
        """Test that base parameters are Ok"""

        self.assertEqual(self.postfeed.link, "/forums/")
        reftitle = "Derniers messages sur {}".format(settings.ZDS_APP["site"]["literal_name"])
        self.assertEqual(self.postfeed.title, reftitle)
        refdescription = "Les derniers messages parus sur le forum de {}.".format(
            settings.ZDS_APP["site"]["literal_name"]
        )
        self.assertEqual(self.postfeed.description, refdescription)

        atom = LastPostsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_getobjects(self):
        """Get object should return the given parameteres in an object"""

        factory = RequestFactory()
        request = factory.get(reverse("forum:post-feed-rss") + "?forum=fofo&tag=tatag")
        obj = self.postfeed.get_object(request=request)
        self.assertEqual(obj["forum"], "fofo")
        self.assertEqual(obj["tag"], "tatag")

    def test_items_success(self):
        """test that right items are sent back according to obj"""

        # test empty obj
        obj = {}
        # should return all topics
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 5)
        # test with a tag
        obj = {"tag": self.tag.pk}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 2)
        # test with a forum
        obj = {"forum": self.topic1.forum.pk}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 2)
        # test with a forum and a tag
        obj = {"forum": self.topic1.forum.pk, "tag": self.tag.pk}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)

    def test_items_bad_cases(self):
        """test that right items are sent back according to obj"""

        # test empty values, return value shoulb be empty
        obj = {"forum": -1, "tag": -1}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        obj = {"forum": -1}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        obj = {"tag": -1}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)
        # with a weird object
        obj = {"forum": "lol"}
        topics = self.postfeed.items(obj=obj)
        self.assertEqual(len(topics), 0)

    def test_get_pubdate(self):
        """test the return value of pubdate"""

        ref = self.post3.pubdate
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_pubdate(item=posts[0])
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """test the return value of title"""

        ref = f"{self.post3.topic.title}, message #{self.post3.pk}"
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_title(item=posts[0])
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """test the return value of description"""

        ref = self.post3.text_html
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_description(item=posts[0])
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """test the return value of author name"""

        ref = self.post3.author.username
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_author_name(item=posts[0])
        self.assertEqual(ret, ref)

    def test_get_author_link(self):
        """test the return value of author link"""

        ref = self.post3.author.get_absolute_url()
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_author_link(item=posts[0])
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """test the return value of item link"""

        ref = self.post3.get_absolute_url()
        posts = self.postfeed.items(obj={"tag": self.tag2.pk})
        ret = self.postfeed.item_link(item=posts[0])
        self.assertEqual(ret, ref)

    def test_content_control_chars(self):
        """
        Test 'control characters' in content of the feed doesn't break it.

        The '\u0007' character in the post content belongs to a character
        family that is  not supported in RSS or Atom feeds and will break their
        generation.
        """
        buggy_topic = TopicFactory(forum=self.forum2, author=self.user)
        post = PostFactory(topic=buggy_topic, author=self.user, position=1)
        post.update_content("Strange char: \u0007")
        post.save()

        request = self.client.get(reverse("forum:post-feed-rss"))
        self.assertEqual(request.status_code, 200)

        request = self.client.get(reverse("forum:post-feed-atom"))
        self.assertEqual(request.status_code, 200)
