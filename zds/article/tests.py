# coding: utf-8

import os
import shutil

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.article.factories import ArticleFactory, ReactionFactory
from zds.article.models import Article, Validation, Reaction, Article
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

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.BOT_ACCOUNT = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.article = ArticleFactory()
        self.article.authors.add(self.user_author)
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
                'version': self.article.sha_draft
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # publish article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
            {
                'article': self.article.pk,
                'comment-v': u'Cet article est excellent',
                'valid-article': 'Demander validation'
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

    def test_alert(self):
        user1 = ProfileFactory().user
        reaction = ReactionFactory(article=self.article, author = user1, position=1)
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        #signal reaction
        result = self.client.post(
            reverse('zds.article.views.edit_reaction') +
            '?message={0}'.format(
                reaction.pk),
            {
                'signal-text': 'Troll',
                'signal-reaction': 'Confirmer',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 1)
        
        # connect with staff
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        #solve alert
        result = self.client.post(
            reverse('zds.article.views.solve_alert'),
            {
                'alert_pk': Alert.objects.first().pk,
                'text': 'Ok',
                'delete-post': 'Resoudre',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 0)
        self.assertEqual(PrivateTopic.objects.filter(author=self.user).count(), 1)
        self.assertEquals(len(mail.outbox), 0)
        
    def test_add_reaction(self):
        """To test add reaction for article."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

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

        reaction1 = ReactionFactory(
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

    def tearDown(self):
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
