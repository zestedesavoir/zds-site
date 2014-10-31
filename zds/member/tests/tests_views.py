# coding: utf-8

import os
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from shutil import rmtree

from zds.settings import SITE_ROOT
from zds.forum.models import TopicFollowed
from zds.member.factories import ProfileFactory, StaffProfileFactory, NonAsciiProfileFactory, UserFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.member.models import Profile
from zds.mp.models import PrivatePost, PrivateTopic
from zds.member.models import TokenRegister, Ban
from zds.tutorial.factories import MiniTutorialFactory
from zds.tutorial.models import PubliableContent, Validation
from zds.article.factories import ArticleFactory
from zds.article.models import Article
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic, Post
from zds.article.models import Validation as ArticleValidation
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.gallery.models import Gallery, UserGallery


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        settings.ZDS_APP['member']['bot_account'] = self.mas.user.username
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
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
            settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
            follow=False)

        self.assertEqual(result.status_code, 200)
        self.assertEquals(len(mail.outbox), 2)

        self.assertTrue(User.objects.get(username='firm1').is_active)

    def test_unregister(self):
        """Tests that unregistering user is working"""

        # test not logged user can't unregister
        self.client.logout()
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
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
        aloneGallery = GalleryFactory()
        UserGalleryFactory(gallery=aloneGallery, user=user.user)
        sharedGallery = GalleryFactory()
        UserGalleryFactory(gallery=sharedGallery, user=user.user)
        UserGalleryFactory(gallery=sharedGallery, user=user2.user)
        # first case : a published tutorial with only one author
        publishedTutorialAlone = MiniTutorialFactory(light=True)
        publishedTutorialAlone.authors.add(user.user)
        publishedTutorialAlone.save()
        # second case : a published tutorial with two authors
        publishedTutorial2 = MiniTutorialFactory(light=True)
        publishedTutorial2.authors.add(user.user)
        publishedTutorial2.authors.add(user2.user)
        publishedTutorial2.save()
        # third case : a private tutorial with only one author
        writingTutorialAlone = MiniTutorialFactory(light=True)
        writingTutorialAlone.authors.add(user.user)
        writingTutorialAlone.save()
        writingTutorialAloneGallerPath = writingTutorialAlone.gallery.get_gallery_path()
        writingTutorialAlonePath = writingTutorialAlone.get_path()
        # fourth case : a private tutorial with at least two authors
        writingTutorial2 = MiniTutorialFactory(light=True)
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
        writingArticle2 = ArticleFactory()
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
        PostFactory(topic=answeredTopic, author=user.user, position=2)
        editedAnswer = PostFactory(topic=answeredTopic, author=user.user, position=3)
        editedAnswer.editor = user.user
        editedAnswer.save()
        privateTopic = PrivateTopicFactory(author=user.user)
        privateTopic.participants.add(user2.user)
        privateTopic.save()
        PrivatePostFactory(author=user.user, privatetopic=privateTopic, position_in_topic=1)
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(publishedTutorialAlone.authors.count(), 1)
        self.assertEqual(publishedTutorialAlone.authors.first().username,
                         settings.ZDS_APP["member"]["external_account"])
        self.assertFalse(os.path.exists(writingTutorialAloneGallerPath))
        self.assertEqual(publishedTutorial2.authors.count(), 1)
        self.assertEqual(publishedTutorial2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"])
                         .count(), 0)
        self.assertIsNotNone(publishedTutorial2.get_prod_path())
        self.assertTrue(os.path.exists(publishedTutorial2.get_prod_path()))
        self.assertIsNotNone(publishedTutorialAlone.get_prod_path())
        self.assertTrue(os.path.exists(publishedTutorialAlone.get_prod_path()))
        self.assertEqual(self.client.get(
            reverse('zds.tutorial.views.view_tutorial_online', args=[
                    publishedTutorialAlone.pk,
                    publishedTutorialAlone.slug]), follow=False).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('zds.tutorial.views.view_tutorial_online', args=[
                    publishedTutorial2.pk,
                    publishedTutorial2.slug]), follow=False).status_code, 200)
        self.assertTrue(os.path.exists(publishedArticleAlone.get_path()))
        self.assertEqual(self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    publishedArticleAlone.pk,
                    publishedArticleAlone.slug]),
            follow=True).status_code, 200)
        self.assertEqual(self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    publishedArticle2.pk,
                    publishedArticle2.slug]),
            follow=True).status_code, 200)
        self.assertEqual(PubliableContent.objects.filter(pk=writingTutorialAlone.pk).count(), 0)
        self.assertEqual(writingTutorial2.authors.count(), 1)
        self.assertEqual(writingTutorial2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"])
                         .count(), 0)
        self.assertEqual(publishedArticleAlone.authors.count(), 1)
        self.assertEqual(publishedArticleAlone.authors
                         .first().username, settings.ZDS_APP["member"]["external_account"])
        self.assertEqual(publishedArticle2.authors.count(), 1)
        self.assertEqual(publishedArticle2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0)
        self.assertEqual(Article.objects.filter(pk=writingArticleAlone.pk).count(), 0)
        self.assertEqual(writingArticle2.authors.count(), 1)
        self.assertEqual(writingArticle2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0)
        self.assertEqual(Topic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(editor__username=user.user.username).count(), 0)
        self.assertEqual(PrivatePost.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(PrivateTopic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertFalse(os.path.exists(writingTutorialAlonePath))
        self.assertIsNotNone(Topic.objects.get(pk=authoredTopic.pk))
        self.assertIsNotNone(PrivateTopic.objects.get(pk=privateTopic.pk))
        self.assertIsNotNone(Gallery.objects.get(pk=aloneGallery.pk))
        self.assertEquals(aloneGallery.get_users().count(), 1)
        self.assertEquals(sharedGallery.get_users().count(), 1)
        self.assertEquals(UserGallery.objects.filter(user=user.user).count(), 0)

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

    def test_promote_interface(self):
        """Test promotion interface"""

        # create users (one regular and one staff and superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()
        tester.user.is_active = False
        tester.user.save()
        staff.user.is_superuser = True
        staff.user.save()

        # create groups
        group = Group.objects.create(name="DummyGroup_1")
        groupbis = Group.objects.create(name="DummyGroup_2")

        # create Forums, Posts and subscribe member to them
        category1 = CategoryFactory(position=1)
        forum1 = ForumFactory(
            category=category1,
            position_in_category=1)
        forum1.group.add(group)
        forum1.save()
        forum2 = ForumFactory(
            category=category1,
            position_in_category=2)
        forum2.group.add(groupbis)
        forum2.save()
        forum3 = ForumFactory(
            category=category1,
            position_in_category=3)
        topic1 = TopicFactory(forum=forum1, author=staff.user)
        topic2 = TopicFactory(forum=forum2, author=staff.user)
        topic3 = TopicFactory(forum=forum3, author=staff.user)

        # LET THE TEST BEGIN !

        # tester shouldn't be able to connect
        login_check = self.client.login(
            username=tester.user.username,
            password='hostel77')
        self.assertEqual(login_check, False)

        # connect as staff (superuser)
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # check that we can go through the page
        result = self.client.get(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}), follow=False)
        self.assertEqual(result.status_code, 200)

        # give user rights and groups thanks to staff (but account still not activated)
        result = self.client.post(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id, groupbis.id],
                'superuser': "on",
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 2)
        self.assertFalse(tester.user.is_active)
        self.assertTrue(tester.user.is_superuser)

        # Now our tester is going to follow one post in every forum (3)
        TopicFollowed(topic=topic1, user=tester.user).save()
        TopicFollowed(topic=topic2, user=tester.user).save()
        TopicFollowed(topic=topic3, user=tester.user).save()

        self.assertEqual(TopicFollowed.objects.filter(user=tester.user).count(), 3)

        # retract all right, keep one group only and activate account
        result = self.client.post(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id],
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 1)
        self.assertTrue(tester.user.is_active)
        self.assertFalse(tester.user.is_superuser)
        self.assertEqual(TopicFollowed.objects.filter(user=tester.user).count(), 2)

        # no groups specified
        result = self.client.post(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh
        self.assertEqual(TopicFollowed.objects.filter(user=tester.user).count(), 1)

        # check that staff can't take away it's own super user rights
        result = self.client.post(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': staff.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        staff = Profile.objects.get(id=staff.id)  # refresh
        self.assertTrue(staff.user.is_superuser)  # still superuser !

        # Finally, check that user can connect and can not access the interface
        login_check = self.client.login(
            username=tester.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('zds.member.views.settings_promote',
                    kwargs={'user_pk': staff.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 403)  # forbidden !

    def test_filter_member_ip(self):
        """Test filter member by ip"""

        # create users (one regular and one staff and superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # test login normal user
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': tester.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # Check that the filter can't be access from normal user
        result = self.client.post(
            reverse('zds.member.views.member_from_ip',
                    kwargs={'ip': tester.last_ip_address}),
            {}, follow=False)
        self.assertEqual(result.status_code, 403)

        # log the staff user
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': staff.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # test that we retrieve correctly the 2 members (staff + user) from this ip
        result = self.client.post(
            reverse('zds.member.views.member_from_ip',
                    kwargs={'ip': staff.last_ip_address}),
            {}, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context['members']), 2)

    def tearDown(self):
        Profile.objects.all().delete()
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            rmtree(settings.MEDIA_ROOT)
        if os.path.isdir(settings.REPO_PATH):
            rmtree(settings.REPO_PATH)
        if os.path.isdir(settings.REPO_PATH_PROD):
            rmtree(settings.REPO_PATH_PROD)
