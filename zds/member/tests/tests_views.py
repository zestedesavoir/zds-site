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
from zds.member.models import Profile, KarmaNote
from zds.mp.models import PrivatePost, PrivateTopic
from zds.member.models import TokenRegister, Ban
from zds.tutorial.factories import MiniTutorialFactory, PublishedMiniTutorial
from zds.tutorial.models import Tutorial
from zds.article.factories import ArticleFactory, PublishedArticleFactory
from zds.article.models import Article
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic, Post
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.gallery.models import Gallery, UserGallery


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['tutorial']['repo_path'] = os.path.join(SITE_ROOT, 'tutoriels-private-test')
overrided_zds_app['tutorial']['repo_public_path'] = os.path.join(SITE_ROOT, 'tutoriels-public-test')
overrided_zds_app['article']['repo_path'] = os.path.join(SITE_ROOT, 'article-data-test')


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        settings.ZDS_APP['member']['bot_account'] = self.mas.user.username
        self.anonymous = UserFactory(
            username=settings.ZDS_APP["member"]["anonymous_account"],
            password="anything")
        self.external = UserFactory(
            username=settings.ZDS_APP["member"]["external_account"],
            password="anything")
        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(
            category=self.category1,
            position_in_category=1)
        self.staff = StaffProfileFactory().user

    def test_list_members(self):
        """
        To test the listing of the members with and without page parameter.
        """

        # list of members.
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # list of members with page parameter.
        result = self.client.get(
            reverse('member-list') + u'?page=1',
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # page which doesn't exist.
        result = self.client.get(
            reverse('member-list') +
            u'?page=1534',
            follow=False
        )
        self.assertEqual(result.status_code, 404)

        # page parameter isn't an integer.
        result = self.client.get(
            reverse('member-list') +
            u'?page=abcd',
            follow=False
        )
        self.assertEqual(result.status_code, 404)

    def test_details_member(self):
        """
        To test details of a member given.
        """

        # details of a staff user.
        result = self.client.get(
            reverse('member-detail', args=[self.staff.username]),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # details of an unknown user.
        result = self.client.get(
            reverse('member-detail', args=['unknown_user']),
            follow=False
        )
        self.assertEqual(result.status_code, 404)

    def test_login(self):
        """
        To test user login.
        """
        user = ProfileFactory()

        # login a user. Good password then redirection to the homepage.
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        self.assertRedirects(result, reverse('zds.pages.views.home'))

        # login failed with bad password then no redirection
        # (status_code equals 200 and not 302).
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel',
             'remember': 'remember'},
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login a user. Good password and next parameter then
        # redirection to the "next" page.
        result = self.client.post(
            reverse('zds.member.views.login_view') +
            '?next=' + reverse('zds.gallery.views.gallery_list'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        self.assertRedirects(result, reverse('zds.gallery.views.gallery_list'))

        # check if the login form will redirect if there is
        # a next parameter.
        self.client.logout()
        result = self.client.get(
            reverse('zds.member.views.login_view') +
            '?next=' + reverse('zds.gallery.views.gallery_list'))
        self.assertContains(result,
                            reverse('zds.member.views.login_view') +
                            '?next=' + reverse('zds.gallery.views.gallery_list'),
                            count=1)

    def test_register(self):
        """
        To test user registration.
        """

        # register a new user.
        result = self.client.post(
            reverse('register-member'),
            {
                'username': 'firm1',
                'password': 'flavour',
                'password_confirm': 'flavour',
                'email': 'firm1@zestedesavoir.com'},
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check email has been sent.
        self.assertEquals(len(mail.outbox), 1)

        # check if the new user is well inactive.
        user = User.objects.get(username='firm1')
        self.assertFalse(user.is_active)

        # make a request on the link which has been sent in mail to
        # confirm the registration.
        token = TokenRegister.objects.get(user=user)
        result = self.client.get(
            settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check a new email has been sent at the new user.
        self.assertEquals(len(mail.outbox), 2)

        # check if the new user is active.
        self.assertTrue(User.objects.get(username='firm1').is_active)

    def test_unregister(self):
        """
        To test that unregistering user is working.
        """

        # test not logged user can't unregister.
        self.client.logout()
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test logged user can register.
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

        # Attach a user at tutorials, articles, topics and private topics. After that,
        # unregister this user and check that he is well removed in all contents.
        user = ProfileFactory()
        user2 = ProfileFactory()
        alone_gallery = GalleryFactory()
        UserGalleryFactory(gallery=alone_gallery, user=user.user)
        shared_gallery = GalleryFactory()
        UserGalleryFactory(gallery=shared_gallery, user=user.user)
        UserGalleryFactory(gallery=shared_gallery, user=user2.user)
        # first case : a published tutorial with only one author
        published_tutorial_alone = PublishedMiniTutorial(light=True)
        published_tutorial_alone.authors.add(user.user)
        published_tutorial_alone.save()
        # second case : a published tutorial with two authors
        published_tutorial_2 = PublishedMiniTutorial(light=True)
        published_tutorial_2.authors.add(user.user)
        published_tutorial_2.authors.add(user2.user)
        published_tutorial_2.save()
        # third case : a private tutorial with only one author
        writing_tutorial_alone = MiniTutorialFactory(light=True)
        writing_tutorial_alone.authors.add(user.user)
        writing_tutorial_alone.save()
        writing_tutorial_alone_galler_path = writing_tutorial_alone.gallery.get_gallery_path()
        writing_tutorial_alone_path = writing_tutorial_alone.get_path()
        # fourth case : a private tutorial with at least two authors
        writing_tutorial_2 = MiniTutorialFactory(light=True)
        writing_tutorial_2.authors.add(user.user)
        writing_tutorial_2.authors.add(user2.user)
        writing_tutorial_2.save()
        self.client.login(username=self.staff.username, password="hostel77")
        # same thing for articles
        published_article_alone = PublishedArticleFactory()
        published_article_alone.authors.add(user.user)
        published_article_alone.save()
        published_article_2 = PublishedArticleFactory()
        published_article_2.authors.add(user.user)
        published_article_2.authors.add(user2.user)
        published_article_2.save()
        writing_article_alone = ArticleFactory()
        writing_article_alone.authors.add(user.user)
        writing_article_alone.save()
        writing_article_2 = ArticleFactory()
        writing_article_2.authors.add(user.user)
        writing_article_2.authors.add(user2.user)
        writing_article_2.save()
        # about posts and topics
        authored_topic = TopicFactory(author=user.user, forum=self.forum11)
        answered_topic = TopicFactory(author=user2.user, forum=self.forum11)
        PostFactory(topic=answered_topic, author=user.user, position=2)
        edited_answer = PostFactory(topic=answered_topic, author=user.user, position=3)
        edited_answer.editor = user.user
        edited_answer.save()
        private_topic = PrivateTopicFactory(author=user.user)
        private_topic.participants.add(user2.user)
        private_topic.save()
        PrivatePostFactory(author=user.user, privatetopic=private_topic, position_in_topic=1)
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('zds.member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(published_tutorial_alone.authors.count(), 1)
        self.assertEqual(published_tutorial_alone.authors.first().username,
                         settings.ZDS_APP["member"]["external_account"])
        self.assertFalse(os.path.exists(writing_tutorial_alone_galler_path))
        self.assertEqual(published_tutorial_2.authors.count(), 1)
        self.assertEqual(published_tutorial_2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"])
                         .count(), 0)
        self.assertIsNotNone(published_tutorial_2.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_2.get_prod_path()))
        self.assertIsNotNone(published_tutorial_alone.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_alone.get_prod_path()))
        self.assertEqual(self.client.get(
            reverse('zds.tutorial.views.view_tutorial_online', args=[
                    published_tutorial_alone.pk,
                    published_tutorial_alone.slug]), follow=False).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('zds.tutorial.views.view_tutorial_online', args=[
                    published_tutorial_2.pk,
                    published_tutorial_2.slug]), follow=False).status_code, 200)
        self.assertTrue(os.path.exists(published_article_alone.get_path()))
        self.assertEqual(self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    published_article_alone.pk,
                    published_article_alone.slug]),
            follow=True).status_code, 200)
        self.assertEqual(self.client.get(
            reverse(
                'zds.article.views.view_online',
                args=[
                    published_article_2.pk,
                    published_article_2.slug]),
            follow=True).status_code, 200)
        self.assertEqual(Tutorial.objects.filter(pk=writing_tutorial_alone.pk).count(), 0)
        self.assertEqual(writing_tutorial_2.authors.count(), 1)
        self.assertEqual(writing_tutorial_2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"])
                         .count(), 0)
        self.assertEqual(published_article_alone.authors.count(), 1)
        self.assertEqual(published_article_alone.authors
                         .first().username, settings.ZDS_APP["member"]["external_account"])
        self.assertEqual(published_article_2.authors.count(), 1)
        self.assertEqual(published_article_2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0)
        self.assertEqual(Article.objects.filter(pk=writing_article_alone.pk).count(), 0)
        self.assertEqual(writing_article_2.authors.count(), 1)
        self.assertEqual(writing_article_2.authors
                         .filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0)
        self.assertEqual(Topic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(editor__username=user.user.username).count(), 0)
        self.assertEqual(PrivatePost.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(PrivateTopic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertFalse(os.path.exists(writing_tutorial_alone_path))
        self.assertIsNotNone(Topic.objects.get(pk=authored_topic.pk))
        self.assertIsNotNone(PrivateTopic.objects.get(pk=private_topic.pk))
        self.assertIsNotNone(Gallery.objects.get(pk=alone_gallery.pk))
        self.assertEquals(alone_gallery.get_linked_users().count(), 1)
        self.assertEquals(shared_gallery.get_linked_users().count(), 1)
        self.assertEquals(UserGallery.objects.filter(user=user.user).count(), 0)

    def test_sanctions(self):
        """
        Test various sanctions.
        """

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
                'ls-text': u'Texte de test pour LS TEMP'},
            follow=False)
        user = Profile.objects.get(id=user_ls_temp.id)   # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNotNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Lecture Seule Temporaire')
        self.assertEqual(ban.text, u'Texte de test pour LS TEMP')
        self.assertEquals(len(mail.outbox), 3)

        # Test: BAN
        user_ban = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}), {
                'ban': '', 'ban-text': u'Texte de test pour BAN'}, follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban définitif')
        self.assertEqual(ban.text, u'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 4)

        # Test: un-BAN
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}),
            {'un-ban': '',
             'unban-text': u'Texte de test pour BAN'},
            follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Autorisation de se connecter')
        self.assertEqual(ban.text, u'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 5)

        # Test: BAN temp
        user_ban_temp = ProfileFactory()
        result = self.client.post(
            reverse('zds.member.views.modify_profile',
                    kwargs={'user_pk': user_ban_temp.user.id}),
            {'ban-temp': '', 'ban-jrs': 10,
             'ban-text': u'Texte de test pour BAN TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ban_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNotNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban Temporaire')
        self.assertEqual(ban.text, u'Texte de test pour BAN TEMP')
        self.assertEquals(len(mail.outbox), 6)

    def test_nonascii(self):
        user = NonAsciiProfileFactory()
        result = self.client.get(reverse('zds.member.views.login_view') + '?next=' +
                                 reverse('member-detail', args=[user.user.username]),
                                 follow=False)
        self.assertEqual(result.status_code, 200)

    def test_promote_interface(self):
        """
        Test promotion interface.
        """

        # create users (one regular, one staff and one superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()
        tester.user.is_active = False
        tester.user.save()
        staff.user.is_superuser = True
        staff.user.save()

        # create groups
        group = Group.objects.create(name="DummyGroup_1")
        groupbis = Group.objects.create(name="DummyGroup_2")

        # create Forums, Posts and subscribe member to them.
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
        """
        Test filter member by ip.
        """

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

    def test_modify_user_karma(self):
        """
        To test karma of a user modified by a staff user.
        """
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # login as user
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': tester.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that user can't use this feature
        result = self.client.post(reverse('zds.member.views.modify_karma'), follow=False)
        self.assertEqual(result.status_code, 403)

        # login as staff
        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': staff.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # try to give a few bad points to the tester
        result = self.client.post(
            reverse('zds.member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Bad tester is bad !',
             'points': '-50'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -50)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 1)

        # Now give a few good points
        result = self.client.post(
            reverse('zds.member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !',
             'points': '10'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 2)

        # Now access some unknow user
        result = self.client.post(
            reverse('zds.member.views.modify_karma'),
            {'profile_pk': -1,
             'warning': 'Good tester is good !',
             'points': '10'},
            follow=False)
        self.assertEqual(result.status_code, 404)

        # Now give unknow point
        result = self.client.post(
            reverse('zds.member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !',
             'points': ''},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 3)

        # Now give no point at all
        result = self.client.post(
            reverse('zds.member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 4)

        # Now access without post
        result = self.client.get(reverse('zds.member.views.modify_karma'), follow=False)
        self.assertEqual(result.status_code, 404)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            rmtree(settings.MEDIA_ROOT)
