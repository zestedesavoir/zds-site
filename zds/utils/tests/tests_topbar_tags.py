from django.contrib.auth.models import Group
from django.test import TestCase

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, TopicFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory, PublishedContentFactory, SubCategoryFactory
from zds.utils.templatetags.topbar import topbar_forum_categories, topbar_publication_categories
from zds.utils.tests.factories import CategoryFactory as ContentCategoryFactory


@override_for_contents()
class TopBarTests(TutorialTestMixin, TestCase):
    def setUp(self):
        # Create some forum's category
        self.category1 = ForumCategoryFactory(position=1)
        self.category2 = ForumCategoryFactory(position=2)

        # Create forum
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)

        # Only for staff
        self.staff1 = StaffProfileFactory()

        self.forum12 = ForumFactory(category=self.category2, position_in_category=2)
        self.forum12.groups.add(Group.objects.filter(name="staff").first())
        self.forum12.save()

        # don't build PDF to speed up the tests

    def test_top_tags(self):
        user = ProfileFactory().user

        # Create 7 topics and give them tags on both public and staff topics
        # in random order to make sure it works
        # tags are named tag-X-Y, where X is the # times it's assigned to a public topic
        # and Y is the total (public + staff) it's been assigned

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({"tag-3-5"})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({"tag-3-5"})
        topic.add_tags({"tag-4-4"})

        topic = TopicFactory(forum=self.forum12, author=self.staff1.user)
        topic.add_tags({"tag-0-1"})
        topic.add_tags({"tag-0-2"})
        topic.add_tags({"tag-3-5"})

        topic = TopicFactory(forum=self.forum12, author=self.staff1.user)
        topic.add_tags({"tag-0-2"})
        topic.add_tags({"tag-3-5"})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({"tag-4-4"})
        topic.add_tags({"tag-3-5"})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({"tag-4-4"})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({"tag-4-4"})

        # Now call the function, should be "tag-4-4", "tag-3-5"
        top_tags = topbar_forum_categories(user).get("tags")

        # tag-X-Y : X should be decreasing
        self.assertEqual(top_tags[0].title, "tag-4-4")
        self.assertEqual(top_tags[1].title, "tag-3-5")
        self.assertEqual(len(top_tags), 2)

        # Admin should see theirs specifics tags
        top_tags = topbar_forum_categories(self.staff1.user).get("tags")

        # tag-X-Y : Y should be decreasing
        self.assertEqual(top_tags[0].title, "tag-3-5")
        self.assertEqual(top_tags[1].title, "tag-4-4")
        self.assertEqual(top_tags[2].title, "tag-0-2")
        self.assertEqual(top_tags[3].title, "tag-0-1")
        self.assertEqual(len(top_tags), 4)

        # Now we want to exclude a tag
        self.overridden_zds_app["forum"]["top_tag_exclu"] = {"tag-4-4"}

        # User only sees the only 'public' tag left
        top_tags = topbar_forum_categories(user).get("tags")
        self.assertEqual(top_tags[0].title, "tag-3-5")
        self.assertEqual(len(top_tags), 1)

    def test_top_tags_content(self):
        tags_tuto = ["a", "b", "c"]
        tags_article = ["a", "d", "e"]

        content = PublishedContentFactory(type="TUTORIAL", author_list=[ProfileFactory().user])
        content.add_tags(tags_tuto)
        content.save()
        tags_tuto = content.tags.all()

        content = PublishedContentFactory(type="ARTICLE", author_list=[ProfileFactory().user])
        content.add_tags(tags_article)
        content.save()
        tags_article = content.tags.all()

        top_tags_tuto = topbar_publication_categories("TUTORIAL").get("tags")
        top_tags_article = topbar_publication_categories("ARTICLE").get("tags")

        self.assertEqual(list(top_tags_tuto), list(tags_tuto))
        self.assertEqual(list(top_tags_article), list(tags_article))

    def test_content_ordering(self):
        category_1 = ContentCategoryFactory()
        category_2 = ContentCategoryFactory()
        subcategory_1 = SubCategoryFactory(category=category_1)
        subcategory_1.position = 5
        subcategory_1.save()
        subcategory_2 = SubCategoryFactory(category=category_1)
        subcategory_2.position = 1
        subcategory_2.save()
        subcategory_3 = SubCategoryFactory(category=category_2)

        tuto_1 = PublishableContentFactory(type="TUTORIAL")
        tuto_1.subcategory.add(subcategory_1)
        tuto_1_draft = tuto_1.load_version()
        publish_content(tuto_1, tuto_1_draft, is_major_update=True)

        top_categories_tuto = topbar_publication_categories("TUTORIAL").get("categories")
        expected = [(subcategory_1.title, subcategory_1.slug, category_1.slug)]
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        tuto_2 = PublishableContentFactory(type="TUTORIAL")
        tuto_2.subcategory.add(subcategory_2)
        tuto_2_draft = tuto_2.load_version()
        publish_content(tuto_2, tuto_2_draft, is_major_update=True)

        top_categories_tuto = topbar_publication_categories("TUTORIAL").get("categories")
        # New subcategory is now first is the list
        expected.insert(0, (subcategory_2.title, subcategory_2.slug, category_1.slug))
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        article_1 = PublishableContentFactory(type="TUTORIAL")
        article_1.subcategory.add(subcategory_3)
        article_1_draft = tuto_2.load_version()
        publish_content(article_1, article_1_draft, is_major_update=True)

        # New article has no impact
        top_categories_tuto = topbar_publication_categories("TUTORIAL").get("categories")
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        top_categories_contents = topbar_publication_categories(["TUTORIAL", "ARTICLE"]).get("categories")
        expected_2 = [(subcategory_3.title, subcategory_3.slug, category_2.slug)]
        self.assertEqual(top_categories_contents[category_1.title], expected)
        self.assertEqual(top_categories_contents[category_2.title], expected_2)
