from copy import deepcopy
import os
import shutil

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory, \
    HelpWriting, Licence
from zds.member.factories import ProfileFactory
from zds.tutorialv2.models.database import PublishableContent, PublishedContent, ContentReaction, \
    Validation as CValidation
from zds.gallery.models import Gallery, UserGallery
from zds.utils.management.commands.load_fixtures import Command as FixtureCommand

BASE_DIR = settings.BASE_DIR

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')
overridden_zds_app['content']['extra_content_generation_policy'] = 'SYNC'
overridden_zds_app['content']['build_pdf_when_published'] = False


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class CommandsTestCase(TestCase):
    def test_load_fixtures(self):

        args = []
        opts = {
            'modules': FixtureCommand.zds_resource_config
        }
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
        args = ['fixtures/advanced/aide_tuto_media.yaml']
        opts = {}
        call_command('load_factory_data', *args, **opts)

        self.assertTrue(HelpWriting.objects.count() > 0)

    def test_profiler(self):
        result = self.client.get('/?prof', follow=True)
        self.assertEqual(result.status_code, 200)

        admin = ProfileFactory()
        admin.user.is_superuser = True
        admin.save()
        self.assertTrue(self.client.login(username=admin.user.username, password='hostel77'))

        result = self.client.get('/?prof', follow=True)
        self.assertEqual(result.status_code, 200)

    def tearDown(self):

        if os.path.isdir(overridden_zds_app['content']['repo_private_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_private_path'])
        if os.path.isdir(overridden_zds_app['content']['repo_public_path']):
            shutil.rmtree(overridden_zds_app['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
