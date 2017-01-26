# coding: utf-8
from django.contrib.auth.models import Group

from django.test import TestCase
from zds import settings

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.utils.templatetags.topbar import top_categories


class TopBarTests(TestCase):

    def setUp(self):

        # Create some forum's category
        self.category1 = CategoryFactory(position=1)
        self.category2 = CategoryFactory(position=2)

        # Create forum
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)

        # Only for staff
        self.staff1 = StaffProfileFactory()

        self.forum12 = ForumFactory(category=self.category2, position_in_category=2)
        self.forum12.group.add(Group.objects.filter(name='staff').first())
        self.forum12.save()

    def test_top_tags(self):
        """Unit testing top_categories method """

        user = ProfileFactory().user

        # Create 7 topics and give them tags on both public and staff topics
        # in random order to make sure it works
        # tags are named tag-X-Y, where X is the # times it's assigned to a public topic
        # and Y is the total (public + staff) it's been assigned

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'tag-3-5'})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'tag-3-5'})
        topic.add_tags({'tag-4-4'})

        topic = TopicFactory(forum=self.forum12, author=self.staff1.user)
        topic.add_tags({'tag-0-1'})
        topic.add_tags({'tag-0-2'})
        topic.add_tags({'tag-3-5'})

        topic = TopicFactory(forum=self.forum12, author=self.staff1.user)
        topic.add_tags({'tag-0-2'})
        topic.add_tags({'tag-3-5'})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'tag-4-4'})
        topic.add_tags({'tag-3-5'})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'tag-4-4'})

        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'tag-4-4'})

        # Now call the function, should be "tag-4-4", "tag-3-5"
        top_tags = top_categories(user).get('tags')

        # tag-X-Y : X should be decreasing
        self.assertEqual(top_tags[0].title, 'tag-4-4')
        self.assertEqual(top_tags[1].title, 'tag-3-5')
        self.assertEqual(len(top_tags), 2)

        # Admin should see theirs specifics tags
        top_tags = top_categories(self.staff1.user).get('tags')

        # tag-X-Y : Y should be decreasing
        self.assertEqual(top_tags[0].title, 'tag-3-5')
        self.assertEqual(top_tags[1].title, 'tag-4-4')
        self.assertEqual(top_tags[2].title, 'tag-0-2')
        self.assertEqual(top_tags[3].title, 'tag-0-1')
        self.assertEqual(len(top_tags), 4)

        # Now we want to exclude a tag
        settings.ZDS_APP['forum']['top_tag_exclu'] = {'tag-4-4'}

        # User only sees the only 'public' tag left
        top_tags = top_categories(user).get('tags')
        self.assertEqual(top_tags[0].title, 'tag-3-5')
        self.assertEqual(len(top_tags), 1)
