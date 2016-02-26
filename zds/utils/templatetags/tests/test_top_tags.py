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
        self.forum12.group.add(Group.objects.filter(name="staff").first())
        self.forum12.save()

    def test_top_tags(self):
        """Unit testing top_categories method """

        user = ProfileFactory().user

        # Create some topics
        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'C#'})

        topic1 = TopicFactory(forum=self.forum11, author=user)
        topic1.add_tags({'C#'})

        topic2 = TopicFactory(forum=self.forum11, author=user)
        topic2.add_tags({'C#'})

        topic3 = TopicFactory(forum=self.forum11, author=user)
        topic3.add_tags({'PHP'})

        topic4 = TopicFactory(forum=self.forum11, author=user)
        topic4.add_tags({'PHP'})

        topic5 = TopicFactory(forum=self.forum12, author=user)
        topic5.add_tags({'stafftag'})

        # Now call the function, should be "C#", "PHP"
        top_tags = top_categories(user).get('tags')

        # Assert
        self.assertEqual(top_tags[0].title, 'c#')
        self.assertEqual(top_tags[1].title, 'php')
        self.assertEqual(len(top_tags), 2)

        # Admin should see theirs specifics tags
        top_tags_for_staff = top_categories(self.staff1.user).get('tags')
        self.assertEqual(top_tags_for_staff[2].title, 'stafftag')

        # Now we want to exclude a tag
        settings.ZDS_APP['forum']['top_tag_exclu'] = {'php'}
        top_tags = top_categories(user).get('tags')

        # Assert that we should only have one tags
        self.assertEqual(top_tags[0].title, 'c#')
        self.assertEqual(len(top_tags), 1)
