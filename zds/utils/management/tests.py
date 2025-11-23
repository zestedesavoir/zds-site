from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.test import TestCase

from zds.forum.models import Forum, ForumCategory, Topic
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.gallery.models import Gallery, UserGallery
from zds.member.models import Profile
from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.models.database import ContentReaction, PublishableContent, PublishedContent
from zds.tutorialv2.models.database import Validation as CValidation
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.utils.management.commands.load_fixtures import Command as FixtureCommand
from zds.utils.models import Category as TCategory
from zds.utils.models import CategorySubCategory, Licence, SubCategory, Tag


@override_for_contents()
class CommandsTestCase(TutorialTestMixin, TestCase):
    def test_load_fixtures(self):
        args = []
        opts = {"modules": FixtureCommand.zds_resource_config}
        call_command("load_fixtures", *args, **opts)

        self.assertTrue(User.objects.count() > 0)
        self.assertTrue(Permission.objects.count() > 0)
        self.assertTrue(Profile.objects.count() > 0)
        self.assertTrue(Forum.objects.count() > 0)
        self.assertTrue(Topic.objects.count() > 0)
        self.assertTrue(ForumCategory.objects.count() > 0)
        self.assertTrue(Tag.objects.count() > 0)
        self.assertTrue(TCategory.objects.count() > 0)
        self.assertTrue(CategorySubCategory.objects.count() > 0)
        self.assertTrue(SubCategory.objects.count() > 0)
        self.assertTrue(Licence.objects.count() > 0)
        self.assertTrue(PublishableContent.objects.count() > 0)
        self.assertTrue(PublishedContent.objects.count() > 0)
        self.assertTrue(ContentReaction.objects.count() > 0)
        self.assertTrue(CValidation.objects.count() > 0)
        self.assertTrue(UserGallery.objects.count() > 0)
        self.assertTrue(Gallery.objects.count() > 0)

    def test_load_factory_data(self):
        args = ["fixtures/advanced/aide_tuto_media.yaml"]
        opts = {}
        call_command("load_factory_data", *args, **opts)

        self.assertTrue(HelpWriting.objects.count() > 0)

    def test_profiler(self):
        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)

        admin = ProfileFactory()
        admin.user.is_superuser = True
        admin.save()
        self.client.force_login(admin.user)

        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)

    def test_remove_old_ip_addresses(self):
        category = ForumCategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        user = ProfileFactory().user
        topic = TopicFactory(forum=forum, author=user)
        old_post = PostFactory(topic=topic, author=user, position=1)
        old_post.pubdate = old_post.pubdate.replace(year=1999)
        old_post.save()
        recent_post = PostFactory(topic=topic, author=user, position=2)

        self.assertNotEqual(old_post.ip_address, "")
        self.assertNotEqual(recent_post.ip_address, "")

        call_command("remove_one_year_old_ip_addresses")
        old_post.refresh_from_db()
        recent_post.refresh_from_db()

        self.assertEqual(old_post.ip_address, "")
        self.assertNotEqual(recent_post.ip_address, "")
