# coding: utf-8
import os
import shutil

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
        settings.BOT_ACCOUNT = self.mas.username

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

    def test_not_delete_image_on_change(self):
        '''test if image IS NOT deleted on change (for versioning)'''

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
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    settings.MEDIA_ROOT, self.article.image.name
                )
            )
        )
        # now that we have a first image, let's change it

        oldAddress = self.article.image.name
        self.article.image = self.logo2
        self.article.save()
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    settings.MEDIA_ROOT, self.article.image.name
                )
            )
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(settings.MEDIA_ROOT, oldAddress)
            )
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
                'licence' : new_licence.pk
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
                'licence' : self.licence.pk
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
                'licence' : new_licence.pk
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
                'licence' : new_licence.pk
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

    def test_versionning_image(self):
        '''test if versionning of thumbnail is active'''

        #json = self.article.load_json()
        
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
                'licence' : self.article.licence.pk
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        article = Article.objects.get(pk=self.article.pk)

    def tearDown(self):
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
