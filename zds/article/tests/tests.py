# coding: utf-8
import os
import shutil
import tempfile
import zipfile
import datetime
from zds.gallery.factories import ImageFactory, UserGalleryFactory, GalleryFactory

from django.contrib import messages
from django.contrib.auth.models import Group

try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.article.factories import ArticleFactory, ReactionFactory,   \
    LicenceFactory, PublishedArticleFactory, SubCategoryFactory
from zds.article.models import Validation, Reaction, Article, Licence
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.mp.models import PrivateTopic
from zds.settings import BASE_DIR
from zds.utils.models import Alert


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['article']['repo_path'] = os.path.join(BASE_DIR, 'article-data-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ArticleTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.licence = LicenceFactory()

        self.article = ArticleFactory()
        self.article.authors.add(self.user_author)
        self.article.licence = self.licence
        self.article.save()

        # connect with user
        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public article
        pub = self.client.post(
            reverse('article-modify'),
            {
                'article': self.article.pk,
                'comment': u'Valides moi ce bébé',
                'pending': 'Demander validation',
                'version': self.article.sha_draft,
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # reserve tutorial
        validation = Validation.objects.get(
            article__pk=self.article.pk)
        pub = self.client.post(
            reverse('article-reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish article
        pub = self.client.post(
            reverse('article-modify'),
            {
                'article': self.article.pk,
                'comment-v': u'Cet article est excellent',
                'valid-article': 'Demander validation',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        mail.outbox = []

        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

    def test_delete_image_on_change(self):
        """test que l'image est bien supprimée quand on la change"""

        root = settings.BASE_DIR
        if not os.path.isdir(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        shutil.copyfile(
            os.path.join(root, 'fixtures', 'logo.png'),
            os.path.join(settings.MEDIA_ROOT, 'logo2.png')
        )
        shutil.copyfile(
            os.path.join(settings.MEDIA_ROOT, 'logo2.png'),
            os.path.join(settings.MEDIA_ROOT, 'logo.png')
        )
        self.logo1 = os.path.join(settings.MEDIA_ROOT, 'logo.png')
        self.logo2 = os.path.join(settings.MEDIA_ROOT, 'logo2.png')

        self.article.image = self.logo1
        self.article.save()
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    settings.MEDIA_ROOT, self.article.image.name
                )
            ),
            True
        )
        # now that we have a first image, let's change it

        old_address = self.article.image.name
        self.article.image = self.logo2
        self.article.save()
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    settings.MEDIA_ROOT, self.article.image.name
                )
            ),
            True
        )
        self.assertEqual(
            os.path.exists(
                os.path.join(settings.MEDIA_ROOT, old_address)
            ),
            False
        )
        os.unlink(self.logo2)
        # shutil.rmtree(settings.MEDIA_ROOT)

    def test_alert(self):
        user1 = ProfileFactory().user
        reaction = ReactionFactory(
            article=self.article,
            author=user1,
            position=1)
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # signal reaction
        result = self.client.post(
            reverse('article-edit-reaction') +
            '?message={0}'.format(
                reaction.pk),
            {
                'signal_text': 'Troll',
                'signal_message': 'Confirmer',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 1)

        # connect with staff
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # solve alert
        result = self.client.post(
            reverse('article-solve-alert'),
            {
                'alert_pk': Alert.objects.first().pk,
                'text': 'Ok',
                'delete_message': 'Resoudre',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 0)
        self.assertEqual(
            PrivateTopic.objects.filter(
                author=self.user).count(),
            1)
        self.assertEquals(len(mail.outbox), 0)

    def test_add_reaction(self):
        """To test add reaction for article."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        # add empty reaction
        result = self.client.post(
            reverse('article-answer') +
            '?article={0}'.format(
                self.article.pk),
            {
                'last_reaction': '0',
                'text': u''},
            follow=False)
        self.assertEqual(result.status_code, 200)
        # check reactions's number
        self.assertEqual(Reaction.objects.all().count(), 0)

        # add reaction
        result = self.client.post(
            reverse('article-answer') +
            '?article={0}'.format(
                self.article.pk),
            {
                'last_reaction': '0',
                'text': u'Histoire de blablater dans les comms de l\'article'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check reactions's number
        self.assertEqual(Reaction.objects.all().count(), 1)

        # check values
        art = Article.objects.get(pk=self.article.pk)
        first_art = Reaction.objects.first()
        self.assertEqual(first_art.article, art)
        self.assertEqual(first_art.author.pk, user1.pk)
        self.assertEqual(first_art.position, 1)
        self.assertEqual(first_art.pk, art.last_reaction.pk)
        self.assertEqual(
            Reaction.objects.first().text,
            u'Histoire de blablater dans les comms de l\'article')

        # test antispam return 403
        result = self.client.post(
            reverse('article-answer') +
            '?article={0}'.format(
                self.article.pk),
            {
                'last_reaction': art.last_reaction.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 403)

        ReactionFactory(
            article=self.article,
            position=2,
            author=self.staff)

        # test more reaction
        result = self.client.post(
            reverse('article-answer') +
            '?article={0}'.format(
                self.article.pk),
            {
                'last_reaction': self.article.last_reaction.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_read_not_public_article(self):
        """To test if nobody can read a not public article."""

        # member can't read public articles which is not published
        article_no_public = ArticleFactory()
        article_no_public.on_line = False
        article_no_public.save()

        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    article_no_public.pk,
                    article_no_public.slug]),
            follow=False)
        self.assertEqual(result.status_code, 404)

        # logout before
        self.client.logout()

        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    article_no_public.pk,
                    article_no_public.slug]),
            follow=False)
        self.assertEqual(result.status_code, 404)

    def test_url_for_guest(self):
        """Test simple get request by guest."""

        # logout before
        self.client.logout()

        # guest can read public articles
        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # guest can't read offline articles
        result = self.client.get(
            reverse(
                'zds.article.views.view',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_url_for_member(self):
        """Test simple get request by simple member."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # member who isn't author can read public articles
        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline articles
        result = self.client.get(
            reverse(
                'zds.article.views.view',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

    def test_url_for_author(self):
        """Test simple get request by author."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # author can read public articles
        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # author can use js
        self.article.js_support = True
        self.article.save()

        result = self.client.get(
            reverse(
                'zds.article.views.view',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_url_for_staff(self):
        """Test simple get request by staff."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # member who isn't author can read public articles
        result = self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline articles
        result = self.client.get(
            reverse(
                'zds.article.views.view',
                args=[
                    self.article.pk,
                    self.article.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_workflow_licence(self):
        """Ensure the behavior of licence on articles"""

        # create a new licence
        new_licence = LicenceFactory(code='CC_BY', title='Creative Commons BY')
        new_licence = Licence.objects.get(pk=new_licence.pk)

        # check value first
        article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(article.licence.pk, self.licence.pk)

        # logout before
        self.client.logout()
        # login with author
        self.assertTrue(
            self.client.login(
                username=self.user_author.username,
                password='hostel77')
        )

        # change licence (get 302) :
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': self.article.title,
                'description': self.article.description,
                'text': self.article.get_text(),
                'subcategory': self.article.subcategory.all(),
                'licence': new_licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        article = Article.objects.get(pk=self.article.pk)
        self.assertNotEqual(article.licence.pk, self.licence.pk)
        self.assertEqual(article.licence.pk, new_licence.pk)

        # test change in JSON :
        json = article.load_json()
        self.assertEquals(json['licence'].code, new_licence.code)

        # then logout ...
        self.client.logout()
        # ... and login with staff
        self.assertTrue(
            self.client.login(
                username=self.staff.username,
                password='hostel77')
        )

        # change licence back to old one (get 302, staff can change licence) :
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': self.article.title,
                'description': self.article.description,
                'text': self.article.get_text(),
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(article.licence.pk, self.licence.pk)
        self.assertNotEqual(article.licence.pk, new_licence.pk)

        # test change in JSON :
        json = article.load_json()
        self.assertEquals(json['licence'].code, self.licence.code)

        # then logout ...
        self.client.logout()

        # change licence (get 302, redirection to login page) :
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': self.article.title,
                'description': self.article.description,
                'text': self.article.get_text(),
                'subcategory': self.article.subcategory.all(),
                'licence': new_licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change (normaly, nothing has) :
        article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(article.licence.pk, self.licence.pk)
        self.assertNotEqual(article.licence.pk, new_licence.pk)

        # login with random user
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password='hostel77')
        )

        # change licence (get 403, random user cannot edit article if not in
        # authors list) :
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': self.article.title,
                'description': self.article.description,
                'text': self.article.get_text(),
                'subcategory': self.article.subcategory.all(),
                'licence': new_licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # test change (normaly, nothing has) :
        article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(article.licence.pk, self.licence.pk)
        self.assertNotEqual(article.licence.pk, new_licence.pk)

        # test change in JSON (normaly, nothing has) :
        json = article.load_json()
        self.assertEquals(json['licence'].code, self.licence.code)

    def test_workflow_archive_article(self):
        """ensure the behavior of archive with an article"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # modify article content and title (NOTE: zipfile does not ensure UTF-8)
        article_title = u'Le titre, mais pas pareil'
        article_content = u'Mais nous c\'est pas pareil ...'
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': article_title,
                'description': self.article.description,
                'text': article_content,
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # now, draft and public version are not the same
        article = Article.objects.get(pk=self.article.pk)
        self.assertNotEqual(article.sha_draft, article.sha_public)

        # fetch archives :
        # 1. draft version
        result = self.client.get(
            reverse('article-download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()
        # 2. online version :
        result = self.client.get(
            reverse('article-download') +
            '?article={0}&online'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        online_zip_path = os.path.join(tempfile.gettempdir(), '__online.zip')
        f = open(online_zip_path, 'w')
        f.write(result.content)
        f.close()

        # now check if modification are in draft version of archive and not in the public one
        draft_zip = zipfile.ZipFile(draft_zip_path, 'r')
        online_zip = zipfile.ZipFile(online_zip_path, 'r')

        # first, test in manifest
        online_manifest = json_reader.loads(online_zip.read('manifest.json'))
        self.assertNotEqual(online_manifest['title'], article_title)  # title has not changed in online version

        draft_manifest = json_reader.loads(draft_zip.read('manifest.json'))
        self.assertNotEqual(online_manifest['title'], article_title)  # title has not changed in online version

        self.assertNotEqual(online_zip.read(online_manifest['text']), article_content)
        self.assertEqual(draft_zip.read(draft_manifest['text']), article_content)  # content is good in draft

        draft_zip.close()
        online_zip.close()

        # then logout and test access
        self.client.logout()

        # public cannot access to draft version of article
        result = self.client.get(
            reverse('article-download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # ... but can access to online version
        result = self.client.get(
            reverse('article-download') +
            '?article={0}&online'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login with random user
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # cannot access to draft version of article (if not author or staff)
        result = self.client.get(
            reverse('article-download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # but can access to online one
        result = self.client.get(
            reverse('article-download') +
            '?article={0}&online'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        self.client.logout()

        # login with staff user
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # staff can access to draft version of article
        result = self.client.get(
            reverse('article-download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        # ... and also to online version
        result = self.client.get(
            reverse('article-download') +
            '?article={0}&online'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # and test also some failing cases

        # When the pk is missing for the edit
        result = self.client.get(
            reverse('article-download') +
            '?&online',
            follow=False)
        self.assertEqual(result.status_code, 404)

        # When the pk is weird
        result = self.client.get(
            reverse('article-download') +
            '?article={abc}&online',
            follow=False)
        self.assertEqual(result.status_code, 404)

        # When the pk is not yet existing
        result = self.client.get(
            reverse('article-download') +
            '?article={424242}&online',
            follow=False)
        self.assertEqual(result.status_code, 404)

        # finally, clean up things:
        os.remove(draft_zip_path)
        os.remove(online_zip_path)

    def test_change_update(self):
        """test the change of `article.update` if modified (ensure #1956)"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        time_0 = datetime.datetime.fromtimestamp(0)  # way deep in the past
        article = Article.objects.get(pk=self.article.pk)
        article.update = time_0
        article.save()

        # first check if this modification is performed :
        self.assertEqual(Article.objects.get(pk=self.article.pk).update, time_0)

        # modify article content and title (implicit call to `maj_repo_article()`)
        article_title = u'Le titre, mais pas pareil'
        article_content = u'Mais nous c\'est pas pareil ...'
        result = self.client.post(
            reverse('article-edit') +
            '?article={}'.format(self.article.pk),
            {
                'title': article_title,
                'description': self.article.description,
                'text': article_content,
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertNotEqual(Article.objects.get(pk=self.article.pk).update, time_0)

        # and also test some failing cases

        # When the pk is missing for the edit
        article_title = u'Le titre, mais pas pareil encore'
        article_content = u'Mais nous c\'est pas pareil encore...'
        result = self.client.post(
            reverse('article-edit'),
            {
                'title': article_title,
                'description': self.article.description,
                'text': article_content,
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 404)

        # When the pk is weird for the edit
        result = self.client.post(
            reverse('article-edit') +
            '?article=' + 'abc',
            {
                'title': article_title,
                'description': self.article.description,
                'text': article_content,
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 404)

        # When the pk is not yet existing for the edit
        result = self.client.post(
            reverse('article-edit') +
            '?article=' + '424242',
            {
                'title': article_title,
                'description': self.article.description,
                'text': article_content,
                'subcategory': self.article.subcategory.all(),
                'licence': self.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 404)

    def test_list_article(self):
        # Test if we can display an article
        result = self.client.get(
            reverse('article-index'),
            {},
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn(self.article.title, result.content)

    def test_list_article_with_subcategory(self):
        # Test with tag restriction

        # Create an article with subcategory
        subcat = SubCategoryFactory()

        article_with_tag = PublishedArticleFactory()
        article_with_tag.subcategory.add(subcat.pk)
        article_with_tag.save()

        # Create another article with another subcategory
        subcat2 = SubCategoryFactory()

        article_with_other_tag = PublishedArticleFactory()
        article_with_other_tag.subcategory.add(subcat2.pk)
        article_with_other_tag.save()

        # Launch test with a subcategory in params url
        result = self.client.post(
            reverse('article-index') + '?tag=' + subcat.slug,
            {},
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertNotIn(self.article.title, result.content)
        self.assertNotIn(article_with_other_tag.title, result.content)
        self.assertIn(article_with_tag.title, result.content)

        # Launch test with no subcategory
        result = self.client.post(
            reverse('article-index') + '?tag=None',
            {},
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn(self.article.title, result.content)
        self.assertIn(article_with_other_tag.title, result.content)
        self.assertIn(article_with_tag.title, result.content)

    def test_new_article(self):
        # Create a Gallery
        gallery = GalleryFactory()

        # Attach an image of a gallery
        image_article = ImageFactory(gallery=gallery)
        UserGalleryFactory(user=self.user_author, gallery=gallery)

        # Create a subcategory
        subcat = SubCategoryFactory()

        # Try the preview button
        result = self.client.post(
            reverse('article-new'),
            {'text': 'A wonderful poetry by Victor Hugo',
             'preview': '',

             'title': '',
             'description': '',
             'text': '',
             'image': image_article.pk,
             'subcategory': subcat.pk,
             'licence': self.licence.pk,
             'msg_commit': ''
             },
            follow=True)
        self.assertEqual(result.status_code, 200)

        # Create an article
        result = self.client.post(
            reverse('article-new'),
            {'title': 'Create a new article test',
             'description': 'Describe the mew article',
             'text': 'A wonderful poetry by Victor Hugo',
             'image': image_article.pk,
             'subcategory': subcat.pk,
             'licence': self.licence.pk,
             'msg_commit': 'Celui qui ouvre une porte d\'école, ferme une prison.'
             },
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Article.objects.filter(title='Create a new article test').count(), 1)

    def test_warn_typo(self):
        """
        Add a non-regression test about warning the author(s) of a typo in an article
        """

        typo_text = u'T\'as fait une faute, t\'es nul'

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # check if author get error when warning typo on its own tutorial
        result = self.client.post(
            reverse('article-warn-typo', args=[self.article.pk]),
            {
                'explication': u'ceci est un test',
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # login with normal user
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse('article-warn-typo', args=[self.article.pk]),
            {
                'explication': typo_text,
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(self.article.get_absolute_url_online(), sent_pm.last_message.text)  # public url is in message

        # Check if we send a wrong pk key
        result = self.client.post(
            reverse('article-warn-typo', args=["1111"]),
            {
                'explication': typo_text,
            },
            follow=False)
        self.assertEqual(result.status_code, 404)

        # Check if we send no explanation
        result = self.client.post(
            reverse('article-warn-typo', args=[self.article.pk]),
            {
                'explication': '',
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # Check if we send an explanation with only space
        result = self.client.post(
            reverse('article-warn-typo', args=[self.article.pk]),
            {
                'explication': '  ',
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # Check if a guest can not warn the author
        self.client.logout()

        result = self.client.post(
            reverse('article-warn-typo', args=[self.article.pk]),
            {
                'explication': typo_text,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
