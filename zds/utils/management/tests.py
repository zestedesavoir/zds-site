from django.core.management import call_command
from django.test import TestCase

from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory, \
    HelpWriting, Licence
from zds.member.factories import ProfileFactory
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent, ContentReaction, \
    Validation as CValidation
from zds.gallery.models import Gallery, UserGallery


class CommandsTestCase(TestCase):
    def test_load_fixtures(self):

        args = []
        opts = {}
        call_command('load_fixtures', *args, **opts)

        self.assertTrue(User.objects.count() > 0)
        self.assertTrue(Permission.objects.count() > 0)
        self.assertTrue(Profile.objects.count() > 0)
        self.assertTrue(Forum.objects.count() > 0)
        self.assertTrue(Topic.objects.count() > 0)
        self.assertTrue(FCategory.objects.count() > 0)
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
        call_command('load_factory_data', *args, **opts)

        self.assertTrue(HelpWriting.objects.count() > 0)

    def test_profiler(self):
        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)

        admin = ProfileFactory()
        admin.user.is_superuser = True
        admin.save()
        self.assertTrue(self.client.login(username=admin.user.username, password='hostel77'))

        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)
