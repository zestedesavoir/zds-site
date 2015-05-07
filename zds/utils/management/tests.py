from django.core.management import call_command
from django.test import TestCase

from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.article.models import Article, Validation as AValidation
from zds.tutorial.models import Tutorial, Validation as TValidation
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory

from zds.member.factories import ProfileFactory


class CommandsTestCase(TestCase):
    def test_load_fixtures(self):

        args = []
        opts = {}
        call_command('load_fixtures', *args, **opts)

        self.assertTrue(User.objects.count() > 0)
        self.assertTrue(Permission.objects.count() > 0)
        self.assertTrue(Profile.objects.count() > 0)
        self.assertTrue(Article.objects.count() > 0)
        self.assertTrue(AValidation.objects.count() > 0)
        self.assertTrue(Tutorial.objects.count() > 0)
        self.assertTrue(TValidation.objects.count() > 0)
        self.assertTrue(Forum.objects.count() > 0)
        self.assertTrue(Topic.objects.count() > 0)
        self.assertTrue(FCategory.objects.count() > 0)
        self.assertTrue(Tag.objects.count() > 0)
        self.assertTrue(TCategory.objects.count() > 0)
        self.assertTrue(CategorySubCategory.objects.count() > 0)
        self.assertTrue(SubCategory.objects.count() > 0)

    def test_profiler(self):
        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)

        admin = ProfileFactory()
        admin.user.is_superuser = True
        admin.save()
        self.assertTrue(self.client.login(username=admin.user.username, password='hostel77'))

        result = self.client.get("/?prof", follow=True)
        self.assertEqual(result.status_code, 200)
