# coding: utf-8
from django.contrib.auth.models import Group

from django.test import TestCase
from django.test.utils import override_settings
import time
from zds import settings

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.utils.templatetags.topbar import top_categories, fetch_top_categories


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'django_cache',
    }
})
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
        top_tags = fetch_top_categories(user).get('tags')

        # Assert
        self.assertEqual(top_tags[0].title, 'c#')
        self.assertEqual(top_tags[1].title, 'php')
        self.assertEqual(len(top_tags), 2)

        # Admin should see theirs specifics tags
        top_tags_for_staff = fetch_top_categories(self.staff1.user).get('tags')
        self.assertEqual(top_tags_for_staff[2].title, 'stafftag')

        # Now we want to exclude a tag
        settings.ZDS_APP['forum']['top_tag_exclu'] = {'php'}
        top_tags = fetch_top_categories(user).get('tags')

        # Assert that we should only have one tags
        self.assertEqual(top_tags[0].title, 'c#')
        self.assertEqual(len(top_tags), 1)

        # Reset exclude tags
        settings.ZDS_APP['forum']['top_tag_exclu'] = {}

        # Now we need to test the cache

        # The cache wait 5 seconds before it expire
        settings.ZDS_APP['forum']['top_tag_cache'] = 5

        # Create cache with staff
        top_tags = top_categories(self.staff1.user)['tags']
        # Create cache with user
        top_tags_user = top_categories(user)['tags']

        # Expect that user didn't see the staff tags
        self.assertEqual(top_tags_user[0].title, 'c#')
        self.assertEqual(top_tags_user[1].title, 'php')
        self.assertEqual(len(top_tags_user), 2)

        # Expect staff see theirs tags
        self.assertEqual(top_tags[0].title, 'c#')
        self.assertEqual(top_tags[1].title, 'php')
        self.assertEqual(top_tags[2].title, 'stafftag')
        self.assertEqual(len(top_tags), 3)

        # Create another tag
        topic = TopicFactory(forum=self.forum11, author=user)
        topic.add_tags({'objectivec'})

        # Expect it not added, since we use cache
        top_tags_user = top_categories(user)['tags']
        self.assertEqual(top_tags_user[0].title, 'c#')
        self.assertEqual(top_tags_user[1].title, 'php')
        self.assertEqual(len(top_tags_user), 2)

        # delays for 5 seconds, wait to the cache to expire
        time.sleep(5)

        # Expect that the cache expired and we get our new tag
        top_tags_user = top_categories(user)['tags']
        self.assertEqual(top_tags_user[0].title, 'c#')
        self.assertEqual(top_tags_user[1].title, 'php')
        self.assertEqual(top_tags_user[2].title, 'objectivec')
        self.assertEqual(len(top_tags_user), 3)
