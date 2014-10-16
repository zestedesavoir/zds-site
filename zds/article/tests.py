# coding: utf-8
import os
import shutil
import tempfile
import zipfile

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
    LicenceFactory
from zds.article.models import Validation, Reaction, Article, Licence
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.mp.models import PrivateTopic
from zds.settings import SITE_ROOT
from zds.utils.models import Alert


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(
    REPO_ARTICLE_PATH=os.path.join(
        SITE_ROOT,
        'articles-data-test'))
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
            reverse('zds.article.views.modify'),
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
            reverse('zds.article.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
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

    def test_delete_image_on_change(self):
        """test que l'image est bien supprimée quand on la change"""

        root = settings.SITE_ROOT
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

        oldAddress = self.article.image.name
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
                os.path.join(settings.MEDIA_ROOT, oldAddress)
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
            reverse('zds.article.views.edit_reaction') +
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
            reverse('zds.article.views.solve_alert'),
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
            reverse('zds.article.views.answer') +
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
            reverse('zds.article.views.answer') +
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
        self.assertEqual(Reaction.objects.get(pk=1).article, art)
        self.assertEqual(Reaction.objects.get(pk=1).author.pk, user1.pk)
        self.assertEqual(Reaction.objects.get(pk=1).position, 1)
        self.assertEqual(Reaction.objects.get(pk=1).pk, art.last_reaction.pk)
        self.assertEqual(
            Reaction.objects.get(
                pk=1).text,
            u'Histoire de blablater dans les comms de l\'article')

        # test antispam return 403
        result = self.client.post(
            reverse('zds.article.views.answer') +
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
            reverse('zds.article.views.answer') +
            '?article={0}'.format(
                self.article.pk),
            {
                'last_reaction': self.article.last_reaction.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 302)

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
        '''Ensure the behavior of licence on articles'''

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
            reverse('zds.article.views.edit') +
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
        self.assertEquals(json['licence'], new_licence.code)

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
            reverse('zds.article.views.edit') +
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
        self.assertEquals(json['licence'], self.licence.code)

        # then logout ...
        self.client.logout()

        # change licence (get 302, redirection to login page) :
        result = self.client.post(
            reverse('zds.article.views.edit') +
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
            reverse('zds.article.views.edit') +
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
        self.assertEquals(json['licence'], self.licence.code)

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
            reverse('zds.article.views.edit') +
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
            reverse('zds.article.views.download') +
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
            reverse('zds.article.views.download') +
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
            reverse('zds.article.views.download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # ... but can access to online version
        result = self.client.get(
            reverse('zds.article.views.download') +
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
            reverse('zds.article.views.download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # but can access to online one
        result = self.client.get(
            reverse('zds.article.views.download') +
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
            reverse('zds.article.views.download') +
            '?article={0}'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        # ... and also to online version
        result = self.client.get(
            reverse('zds.article.views.download') +
            '?article={0}&online'.format(
                self.article.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # finally, clean up things:
        os.remove(draft_zip_path)
        os.remove(online_zip_path)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
