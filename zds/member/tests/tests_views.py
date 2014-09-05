# coding: utf-8

import urllib
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from datetime import datetime
from zds.settings import ANONYMOUS_USER, EXTERNAL_USER, SITE_ROOT

from zds.member.factories import ProfileFactory, StaffProfileFactory, NonAsciiProfileFactory, UserFactory
from zds.member.forms import RegisterForm, ChangeUserForm, ChangePasswordForm
from zds.member.models import Profile
from zds.mp.models import PrivatePost, PrivateTopic
from zds.member.models import TokenRegister, Ban
from zds.tutorial.factories import MiniTutorialFactory
from zds.tutorial.models import Tutorial, Validation
from zds.article.factories import ArticleFactory
from zds.article.models import Article
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic, Post
from zds.article.models import Validation as ArticleValidation

@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(
REPO_PATH_PROD=os.path.join(
SITE_ROOT,
'tutoriels-public-test'))
@override_settings(
REPO_ARTICLE_PATH=os.path.join(
SITE_ROOT,
'articles-data-test'))
class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        settings.BOT_ACCOUNT = self.mas.user.username
        self.anonymous = UserFactory(username=ANONYMOUS_USER, password="anything")
        self.external = UserFactory(username=EXTERNAL_USER, password="anything")
        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(
            category=self.category1,
            position_in_category=1)
        self.staff = StaffProfileFactory().user

    def test_login(self):
        """To test user login."""
        user = ProfileFactory()

        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel',
             'remember': 'remember'},
            follow=False)
        # bad password then no redirection
        self.assertEqual(result.status_code, 200)

        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

    def test_register(self):
        """To test user registration."""

        result = self.client.post(
            reverse('zds.member.views.register_view'),
            {
                'username': 'firm1',
                'password': 'flavour',
                'password_confirm': 'flavour',
                'email': 'firm1@zestedesavoir.com'},
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 1)

        # clic on the link which has been sent in mail
        user = User.objects.get(username='firm1')
        self.assertFalse(user.is_active)

        token = TokenRegister.objects.get(user=user)
        result = self.client.get(
            settings.SITE_URL + token.get_absolute_url(),
            follow=False)

        self.assertEqual(result.status_code, 200)
        self.assertEquals(len(mail.outbox), 2)

        self.assertTrue(User.objects.get(username='firm1').is_active)

    def test_unregister(self):
        """Tests that unregistering user is working"""
        user = ProfileFactory()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 0)
        user = ProfileFactory()
        user2 = ProfileFactory()
        # first case : a published tutorial with only one author
        publishedTutorialAlone = MiniTutorialFactory()
        publishedTutorialAlone.authors.add(user.user)
        publishedTutorialAlone.save()
        # second case : a published tutorial with two authors
        publishedTutorial2 = MiniTutorialFactory()
        publishedTutorial2.authors.add(user.user)
        publishedTutorial2.authors.add(user2.user)
        publishedTutorial2.save()
        # third case : a private tutorial with only one author
        writingTutorialAlone = MiniTutorialFactory()
        writingTutorialAlone.authors.add(user.user)
        writingTutorialAlone.save()
        writingTutorialAlonePath = writingTutorialAlone.get_path()
        # fourth case : a private tutorial with at least two authors
        writingTutorial2 = MiniTutorialFactory()
        writingTutorial2.authors.add(user.user)
        writingTutorial2.authors.add(user2.user)
        writingTutorial2.save()
        self.client.login(username=self.staff.username, password="hostel77")
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': publishedTutorialAlone.pk,
                'text': u'Ce tuto est excellent',
                'version': publishedTutorialAlone.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=publishedTutorialAlone.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # publish tutorial
        pub = self.client.post(
        reverse('zds.tutorial.views.valid_tutorial'),
           {
               'tutorial': publishedTutorialAlone.pk,
               'text': u'Ce tuto est excellent',
               'is_major': True,
               'source': 'http://zestedesavoir.com',
           },
           follow=False)
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': publishedTutorial2.pk,
                'text': u'Ce tuto est excellent',
                'version': publishedTutorial2.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=publishedTutorial2.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # publish tutorial
        pub = self.client.post(
        reverse('zds.tutorial.views.valid_tutorial'),
           {
               'tutorial': publishedTutorial2.pk,
               'text': u'Ce tuto est excellent',
               'is_major': True,
               'source': 'http://zestedesavoir.com',
           },
           follow=False)
        # same thing for articles
        publishedArticleAlone = ArticleFactory()
        publishedArticleAlone.authors.add(user.user)
        publishedArticleAlone.save()
        publishedArticle2 = ArticleFactory()
        publishedArticle2.authors.add(user.user)
        publishedArticle2.authors.add(user2.user)
        publishedArticle2.save()

        writingArticleAlone = ArticleFactory()
        writingArticleAlone.authors.add(user.user)
        writingArticleAlone.save()
        writingArticle2 = MiniTutorialFactory()
        writingArticle2.authors.add(user.user)
        writingArticle2.authors.add(user2.user)
        writingArticle2.save()
        # ask public article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
            {
                'article': publishedArticleAlone.pk,
                'comment': u'Valides moi ce bébé',
                'pending': 'Demander validation',
                'version': publishedArticleAlone.sha_draft,
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)


        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # reserve article
        validation = ArticleValidation.objects.get(
            article__pk=publishedArticleAlone.pk)
        pub = self.client.post(
            reverse('zds.article.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
            {
                'article': publishedArticleAlone.pk,
                'comment-v': u'Cet article est excellent',
                'valid-article': 'Demander validation',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # ask public article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
            {
                'article': publishedArticle2.pk,
                'comment': u'Valides moi ce bébé',
                'pending': 'Demander validation',
                'version': publishedArticle2.sha_draft,
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # reserve article
        validation = ArticleValidation.objects.get(
            article__pk=publishedArticle2.pk)
        pub = self.client.post(
            reverse('zds.article.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish article
        pub = self.client.post(
            reverse('zds.article.views.modify'),
            {
                'article': publishedArticle2.pk,
                'comment-v': u'Cet article est excellent',
                'valid-article': 'Demander validation',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        # about posts and topics
        authoredTopic = TopicFactory(author=user.user, forum=self.forum11)
        answeredTopic = TopicFactory(author=user2.user, forum=self.forum11)
        answer = PostFactory(topic=answeredTopic, author=user.user, position=2)
        editedAnswer = PostFactory(topic=answeredTopic, author=user.user, position=3)
        editedAnswer.editor = user.user
        editedAnswer.save()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(publishedTutorialAlone.authors.count(), 1)
        self.assertEqual(publishedTutorialAlone.authors.first().username, EXTERNAL_USER)
        self.assertEqual(publishedTutorial2.authors.count(), 1)
        self.assertEqual(publishedTutorial2.authors.filter(username=EXTERNAL_USER).count(), 0)
        self.assertEqual(Tutorial.objects.filter(pk=writingTutorialAlone.pk).count(), 0)
        self.assertEqual(writingTutorial2.authors.count(), 1)
        self.assertEqual(writingTutorial2.authors.filter(username=EXTERNAL_USER).count(), 0)
        self.assertEqual(publishedArticleAlone.authors.count(), 1)
        self.assertEqual(publishedArticleAlone.authors.first().username, EXTERNAL_USER)
        self.assertEqual(publishedArticle2.authors.count(), 1)
        self.assertEqual(publishedArticle2.authors.filter(username=EXTERNAL_USER).count(), 0)
        self.assertEqual(Article.objects.filter(pk=writingArticleAlone.pk).count(), 0)
        self.assertEqual(writingArticle2.authors.count(), 1)
        self.assertEqual(writingArticle2.authors.filter(username=EXTERNAL_USER).count(), 0)
        self.assertEqual(Topic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(editor__username=user.user.username).count(), 0)
        self.assertEqual(PrivatePost.objects.filter(author__username=user.user.username).count(),0)
        self.assertEqual(PrivateTopic.objects.filter(author__username=user.user.username).count(),0)
        self.assertFalse(os.path.exists(writingTutorialAlonePath))

    def test_sanctions(self):
        """Test various sanctions."""

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # Test: LS
        user_ls = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-pubdate')[0]
        self.assertEqual(ban.type, 'Lecture Seule')
        self.assertEqual(ban.text, 'Texte de test pour LS')
        self.assertEquals(len(mail.outbox), 1)

        # Test: Un-LS
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'un-ls': '', 'unls-text': 'Texte de test pour un-LS'},
            follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Autorisation d\'écrire')
        self.assertEqual(ban.text, 'Texte de test pour un-LS')
        self.assertEquals(len(mail.outbox), 2)

        # Test: LS temp
        user_ls_temp = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls_temp.user.id}), {
                'ls-temp': '', 'ls-jrs': 10,
                'ls-temp-text': 'Texte de test pour LS TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ls_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNotNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Lecture Seule Temporaire')
        self.assertEqual(ban.text, 'Texte de test pour LS TEMP')
        self.assertEquals(len(mail.outbox), 3)

        # Test: BAN
        user_ban = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}), {
                'ban': '', 'ban-text': 'Texte de test pour BAN'}, follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban définitif')
        self.assertEqual(ban.text, 'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 4)

        # Test: un-BAN
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}),
            {'un-ban': '',
             'unban-text': 'Texte de test pour BAN'},
            follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Autorisation de se connecter')
        self.assertEqual(ban.text, 'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 5)

        # Test: BAN temp
        user_ban_temp = ProfileFactory()
        result = self.client.post(
            reverse('zds.member.views.modify_profile',
                    kwargs={'user_pk': user_ban_temp.user.id}),
            {'ban-temp': '', 'ban-jrs': 10,
             'ban-temp-text': 'Texte de test pour BAN TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ban_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNotNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Ban Temporaire')
        self.assertEqual(ban.text, 'Texte de test pour BAN TEMP')
        self.assertEquals(len(mail.outbox), 6)

    def test_nonascii(self):
        user = NonAsciiProfileFactory()
        result = self.client.get(reverse('zds.member.views.login_view') + '?next='
                                        + reverse('zds.member.views.details', args=[user.user.username]),
                                 follow=False)
        self.assertEqual(result.status_code, 200)

    def tearDown(self):
        Profile.objects.all().delete()
