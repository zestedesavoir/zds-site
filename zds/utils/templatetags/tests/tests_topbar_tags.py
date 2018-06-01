import os
import shutil

from django.contrib.auth.models import Group

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory, PublishableContentFactory, SubCategoryFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.utils.factories import CategoryFactory as ContentCategoryFactory
from zds.utils.templatetags.topbar import top_categories, top_categories_content
from copy import deepcopy


overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')
overridden_zds_app['content']['build_pdf_when_published'] = False


@override_settings(ZDS_APP=overridden_zds_app)
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
        overridden_zds_app['forum']['top_tag_exclu'] = {'tag-4-4'}

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

        tuto_1 = PublishableContentFactory(type='TUTORIAL')
        tuto_1.subcategory.add(subcategory_1)
        tuto_1_draft = tuto_1.load_version()
        publish_content(tuto_1, tuto_1_draft, is_major_update=True)

        top_categories_tuto = top_categories_content('TUTORIAL').get('categories')
        expected = [(subcategory_1.title, subcategory_1.slug, category_1.slug)]
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        tuto_2 = PublishableContentFactory(type='TUTORIAL')
        tuto_2.subcategory.add(subcategory_2)
        tuto_2_draft = tuto_2.load_version()
        publish_content(tuto_2, tuto_2_draft, is_major_update=True)

        top_categories_tuto = top_categories_content('TUTORIAL').get('categories')
        # New subcategory is now first is the list
        expected.insert(0, (subcategory_2.title, subcategory_2.slug, category_1.slug))
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        article_1 = PublishableContentFactory(type='TUTORIAL')
        article_1.subcategory.add(subcategory_3)
        article_1_draft = tuto_2.load_version()
        publish_content(article_1, article_1_draft, is_major_update=True)

        # New article has no impact
        top_categories_tuto = top_categories_content('TUTORIAL').get('categories')
        self.assertEqual(top_categories_tuto[category_1.title], expected)

        top_categories_contents = top_categories_content(['TUTORIAL', 'ARTICLE']).get('categories')
        expected_2 = [(subcategory_3.title, subcategory_3.slug, category_2.slug)]
        self.assertEqual(top_categories_contents[category_1.title], expected)
        self.assertEqual(top_categories_contents[category_2.title], expected_2)

    def tearDown(self):

        if os.path.isdir(overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
