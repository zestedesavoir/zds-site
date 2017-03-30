# coding: utf-8
import os
import shutil

from django.contrib.auth.models import Group

from django.test import TestCase
from django.test.utils import override_settings
from zds import settings

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.settings import BASE_DIR
from zds.tutorialv2.factories import PublishedContentFactory
from zds.utils.templatetags.topbar import top_categories, top_categories_content

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(ZDS_APP=overrided_zds_app)
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
        self.forum12.groups.add(Group.objects.filter(name='staff').first())
        self.forum12.save()

        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

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

    def test_top_tags_content(self):
        """Unit testing top_categories_content method """

        tags_tuto = ['a', 'b', 'c']
        tags_article = ['a', 'd', 'e']

        content = PublishedContentFactory(type='TUTORIAL', author_list=[ProfileFactory().user])
        content.add_tags(tags_tuto)
        content.save()
        tags_tuto = content.tags.all()

        content = PublishedContentFactory(type='ARTICLE', author_list=[ProfileFactory().user])
        content.add_tags(tags_article)
        content.save()
        tags_article = content.tags.all()

        top_tags_tuto = top_categories_content('TUTORIAL').get('tags')
        top_tags_article = top_categories_content('ARTICLE').get('tags')

        self.assertEqual(list(top_tags_tuto), list(tags_tuto))
        self.assertEqual(list(top_tags_article), list(tags_article))

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-active PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True
