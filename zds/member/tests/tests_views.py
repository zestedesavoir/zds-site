# coding: utf-8

from datetime import datetime
import os
import shutil

from oauth2_provider.models import AccessToken, Application

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

from zds.settings import BASE_DIR
from zds.notification.models import TopicAnswerSubscription
from zds.member.factories import ProfileFactory, StaffProfileFactory, NonAsciiProfileFactory, UserFactory, \
    DevProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.member.models import Profile, KarmaNote, TokenForgotPassword
from zds.mp.models import PrivatePost, PrivateTopic
from zds.member.models import TokenRegister, Ban, NewEmailProvider, BannedEmailProvider
from zds.tutorialv2.factories import PublishableContentFactory, PublishedContentFactory, BetaContentFactory
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import Topic, Post
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.gallery.models import Gallery, UserGallery
from zds.utils.models import CommentVote


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        settings.ZDS_APP['member']['bot_account'] = self.mas.user.username
        self.anonymous = UserFactory(
            username=settings.ZDS_APP['member']['anonymous_account'],
            password='anything')
        self.external = UserFactory(
            username=settings.ZDS_APP['member']['external_account'],
            password='anything')
        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(
            category=self.category1,
            position_in_category=1)
        self.staff = StaffProfileFactory().user

        self.bot = Group(name=settings.ZDS_APP['member']['bot_group'])
        self.bot.save()

    def test_karma(self):
        user = ProfileFactory()
        other_user = ProfileFactory()
        self.client.login(
            username=other_user.user.username,
            password='hostel77'
        )
        r = self.client.post(reverse('member-modify-karma'), {
            'profile_pk': user.pk,
            'karma': 42,
            'note': 'warn'
        })
        self.assertEqual(403, r.status_code)
        self.client.logout()
        self.client.login(
            username=self.staff.username,
            password='hostel77'
        )
        # bad id
        r = self.client.post(reverse('member-modify-karma'), {
            'profile_pk': 'blah',
            'karma': 42,
            'note': 'warn'
        }, follow=True)
        self.assertEqual(404, r.status_code)
        # good karma
        r = self.client.post(reverse('member-modify-karma'), {
            'profile_pk': user.pk,
            'karma': 42,
            'note': 'warn'
        }, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertIn('{} : 42'.format(_('Modification du karma')), r.content.decode('utf-8'))
        # more than 100 karma must unvalidate the karma
        r = self.client.post(reverse('member-modify-karma'), {
            'profile_pk': user.pk,
            'karma': 420,
            'note': 'warn'
        }, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertNotIn('{} : 420'.format(_('Modification du karma')), r.content.decode('utf-8'))
        # empty warning must unvalidate the karma
        r = self.client.post(reverse('member-modify-karma'), {
            'profile_pk': user.pk,
            'karma': 41,
            'note': ''
        }, follow=True)
        self.assertEqual(200, r.status_code)
        self.assertNotIn('{} : 41'.format(_('Modification du karma')), r.content.decode('utf-8'))

    def test_list_members(self):
        """
        To test the listing of the members with and without page parameter.
        """

        # create strange member
        weird = ProfileFactory()
        weird.user.username = u'ïtrema718'
        weird.user.email = u'foo@\xfbgmail.com'
        weird.user.save()

        # list of members.
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        nb_users = len(result.context['members'])

        # Test that inactive user don't show up
        unactive_user = ProfileFactory()
        unactive_user.user.is_active = False
        unactive_user.user.save()
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context['members']))

        # Add a Bot and check that list didn't change
        bot_profile = ProfileFactory()
        bot_profile.user.groups.add(self.bot)
        bot_profile.user.save()
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context['members']))

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

    def test_moderation_history(self):
        user = ProfileFactory().user

        ban = Ban(
            user=user,
            moderator=self.staff,
            type='Lecture Seule Temporaire',
            note='Test de LS',
            pubdate=datetime.now(),
        )
        ban.save()

        note = KarmaNote(
            user=user,
            moderator=self.staff,
            karma=5,
            note='Test de karma',
            pubdate=datetime.now(),
        )
        note.save()

        # staff rights are required to view the history, check that
        self.client.logout()
        self.client.login(username=user.username, password='hostel77')
        result = self.client.get(
            user.profile.get_absolute_url(),
            follow=False
        )
        self.assertNotContains(result, 'Historique de modération')

        self.client.logout()
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.get(
            user.profile.get_absolute_url(),
            follow=False
        )
        self.assertContains(result, 'Historique de modération')

        # check that the note and the sanction are in the context
        self.assertIn(ban, result.context['actions'])
        self.assertIn(note, result.context['actions'])

        # and are displayed
        self.assertContains(result, 'Test de LS')
        self.assertContains(result, 'Test de karma')

    def test_profile_page_of_weird_member_username(self):

        # create some user with weird username
        user_1 = ProfileFactory()
        user_2 = ProfileFactory()
        user_3 = ProfileFactory()
        user_1.user.username = u'ïtrema'
        user_1.user.save()
        user_2.user.username = u'&#34;a'
        user_2.user.save()
        user_3.user.username = u'_`_`_`_'
        user_3.user.save()

        # profile pages of weird users.
        result = self.client.get(
            reverse('member-detail', args=[user_1.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse('member-detail', args=[user_2.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse('member-detail', args=[user_3.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)

    def test_modify_member(self):
        user = ProfileFactory().user

        # we need staff right for update other profile, so a member who is not staff can't access to the page
        self.client.logout()
        self.client.login(username=user.username, password='hostel77')

        result = self.client.get(
            reverse('member-settings-mini-profile', args=['xkcd']),
            follow=False
        )
        self.assertEqual(result.status_code, 403)

        self.client.logout()
        self.client.login(username=self.staff.username, password='hostel77')

        # an inexistant member return 404
        result = self.client.get(
            reverse('member-settings-mini-profile', args=['xkcd']),
            follow=False
        )
        self.assertEqual(result.status_code, 404)

        # an existant member return 200
        result = self.client.get(
            reverse('member-settings-mini-profile', args=[self.mas.user.username]),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

    def test_success_preview_biography(self):

        member = ProfileFactory()
        self.client.login(
            username=member.user.username,
            password='hostel77'
        )

        response = self.client.post(
            reverse('update-member'),
            {
                'text': 'It is **my** life',
                'preview': '',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        result_string = ''.join(response.streaming_content)
        self.assertIn('<strong>my</strong>', result_string, 'We need the biography to be properly formatted')

    def test_login(self):
        """
        To test user login.
        """
        user = ProfileFactory()

        # login a user. Good password then redirection to the homepage.
        result = self.client.post(
            reverse('member-login'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        self.assertRedirects(result, reverse('homepage'))

        # login failed with bad password then no redirection
        # (status_code equals 200 and not 302).
        result = self.client.post(
            reverse('member-login'),
            {'username': user.user.username,
             'password': 'hostel',
             'remember': 'remember'},
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login a user. Good password and next parameter then
        # redirection to the "next" page.
        result = self.client.post(
            reverse('member-login') +
            '?next=' + reverse('gallery-list'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        self.assertRedirects(result, reverse('gallery-list'))

        # check if the login form will redirect if there is
        # a next parameter.
        self.client.logout()
        result = self.client.get(
            reverse('member-login') +
            '?next=' + reverse('gallery-list'))
        self.assertContains(result,
                            reverse('member-login') +
                            '?next=' + reverse('gallery-list'),
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

        # check a new email hasn't been sent at the new user.
        self.assertEquals(len(mail.outbox), 1)

        # check if the new user is active.
        self.assertTrue(User.objects.get(username='firm1').is_active)

    def test_unregister(self):
        """
        To test that unregistering user is working.
        """

        # test not logged user can't unregister.
        self.client.logout()
        result = self.client.post(
            reverse('member-unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test logged user can register.
        user = ProfileFactory()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member-unregister'),
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
        published_tutorial_alone = PublishedContentFactory(type='TUTORIAL')
        published_tutorial_alone.authors.add(user.user)
        published_tutorial_alone.save()
        # second case : a published tutorial with two authors
        published_tutorial_2 = PublishedContentFactory(type='TUTORIAL')
        published_tutorial_2.authors.add(user.user)
        published_tutorial_2.authors.add(user2.user)
        published_tutorial_2.save()
        # third case : a private tutorial with only one author
        writing_tutorial_alone = PublishableContentFactory(type='TUTORIAL')
        writing_tutorial_alone.authors.add(user.user)
        writing_tutorial_alone.save()
        writing_tutorial_alone_galler_path = writing_tutorial_alone.gallery.get_gallery_path()
        # fourth case : a private tutorial with at least two authors
        writing_tutorial_2 = PublishableContentFactory(type='TUTORIAL')
        writing_tutorial_2.authors.add(user.user)
        writing_tutorial_2.authors.add(user2.user)
        writing_tutorial_2.save()
        self.client.login(username=self.staff.username, password='hostel77')
        # same thing for articles
        published_article_alone = PublishedContentFactory(type='ARTICLE')
        published_article_alone.authors.add(user.user)
        published_article_alone.save()
        published_article_2 = PublishedContentFactory(type='ARTICLE')
        published_article_2.authors.add(user.user)
        published_article_2.authors.add(user2.user)
        published_article_2.save()
        writing_article_alone = PublishableContentFactory(type='ARTICLE')
        writing_article_alone.authors.add(user.user)
        writing_article_alone.save()
        writing_article_2 = PublishableContentFactory(type='ARTICLE')
        writing_article_2.authors.add(user.user)
        writing_article_2.authors.add(user2.user)
        writing_article_2.save()
        # beta content
        beta_forum = ForumFactory(category=CategoryFactory())
        beta_content = BetaContentFactory(author_list=[user.user], forum=beta_forum)
        beta_content_2 = BetaContentFactory(author_list=[user.user, user2.user], forum=beta_forum)
        # about posts and topics
        authored_topic = TopicFactory(author=user.user, forum=self.forum11)
        answered_topic = TopicFactory(author=user2.user, forum=self.forum11)
        PostFactory(topic=answered_topic, author=user.user, position=2)
        edited_answer = PostFactory(topic=answered_topic, author=user.user, position=3)
        edited_answer.editor = user.user
        edited_answer.save()

        upvoted_answer = PostFactory(topic=answered_topic, author=user2.user, position=4)
        upvoted_answer.like += 1
        upvoted_answer.save()
        CommentVote.objects.create(user=user.user, comment=upvoted_answer, positive=True)

        private_topic = PrivateTopicFactory(author=user.user)
        private_topic.participants.add(user2.user)
        private_topic.save()
        PrivatePostFactory(author=user.user, privatetopic=private_topic, position_in_topic=1)

        # add API key
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(AccessToken.objects.count(), 0)
        api_application = Application()
        api_application.client_id = 'foobar'
        api_application.user = user.user
        api_application.client_type = 'confidential'
        api_application.authorization_grant_type = 'password'
        api_application.client_secret = '42'
        api_application.save()
        token = AccessToken()
        token.user = user.user
        token.token = 'r@d0m'
        token.application = api_application
        token.expires = datetime.now()
        token.save()
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(AccessToken.objects.count(), 1)

        # add a karma note and a sanction with this user
        note = KarmaNote(moderator=user.user, user=user2.user, note='Good!', karma=5)
        note.save()
        ban = Ban(moderator=user.user, user=user2.user, type='Ban définitif', note='Test')
        ban.save()

        # login and unregister:
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member-unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that the bot have taken authorship of tutorial:
        self.assertEqual(published_tutorial_alone.authors.count(), 1)
        self.assertEqual(published_tutorial_alone.authors.first().username,
                         settings.ZDS_APP['member']['external_account'])
        self.assertFalse(os.path.exists(writing_tutorial_alone_galler_path))
        self.assertEqual(published_tutorial_2.authors.count(), 1)
        self.assertEqual(published_tutorial_2.authors
                         .filter(username=settings.ZDS_APP['member']['external_account'])
                         .count(), 0)

        # check that published tutorials remain published and accessible
        self.assertIsNotNone(published_tutorial_2.public_version.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_2.public_version.get_prod_path()))
        self.assertIsNotNone(published_tutorial_alone.public_version.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_alone.public_version.get_prod_path()))
        self.assertEqual(self.client.get(
            reverse('tutorial:view', args=[
                    published_tutorial_alone.pk,
                    published_tutorial_alone.slug]), follow=False).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('tutorial:view', args=[
                    published_tutorial_2.pk,
                    published_tutorial_2.slug]), follow=False).status_code, 200)

        # test that published articles remain accessible
        self.assertTrue(os.path.exists(published_article_alone.public_version.get_prod_path()))
        self.assertEqual(self.client.get(
            reverse(
                'article:view',
                args=[
                    published_article_alone.pk,
                    published_article_alone.slug]),
            follow=True).status_code, 200)
        self.assertEqual(self.client.get(
            reverse(
                'article:view',
                args=[
                    published_article_2.pk,
                    published_article_2.slug]),
            follow=True).status_code, 200)

        # check that the tutorial for which the author was alone does not exists anymore
        self.assertEqual(PublishableContent.objects.filter(pk=writing_tutorial_alone.pk).count(), 0)
        self.assertFalse(os.path.exists(writing_tutorial_alone.get_repo_path()))

        # check that bot haven't take the authorship of the tuto with more than one author
        self.assertEqual(writing_tutorial_2.authors.count(), 1)
        self.assertEqual(writing_tutorial_2.authors
                         .filter(username=settings.ZDS_APP['member']['external_account'])
                         .count(), 0)

        # authorship for the article for which user was the only author
        self.assertEqual(published_article_alone.authors.count(), 1)
        self.assertEqual(published_article_alone.authors
                         .first().username, settings.ZDS_APP['member']['external_account'])
        self.assertEqual(published_article_2.authors.count(), 1)

        self.assertEqual(PublishableContent.objects.filter(pk=writing_article_alone.pk).count(), 0)
        self.assertFalse(os.path.exists(writing_article_alone.get_repo_path()))

        # not bot if another author:
        self.assertEqual(published_article_2.authors
                         .filter(username=settings.ZDS_APP['member']['external_account']).count(), 0)
        self.assertEqual(writing_article_2.authors.count(), 1)
        self.assertEqual(writing_article_2.authors
                         .filter(username=settings.ZDS_APP['member']['external_account']).count(), 0)

        # topics, gallery and PMs:
        self.assertEqual(Topic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(editor__username=user.user.username).count(), 0)
        self.assertEqual(PrivatePost.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(PrivateTopic.objects.filter(author__username=user.user.username).count(), 0)

        self.assertIsNotNone(Topic.objects.get(pk=authored_topic.pk))
        self.assertIsNotNone(PrivateTopic.objects.get(pk=private_topic.pk))
        self.assertIsNotNone(Gallery.objects.get(pk=alone_gallery.pk))
        self.assertEquals(alone_gallery.get_linked_users().count(), 1)
        self.assertEquals(shared_gallery.get_linked_users().count(), 1)
        self.assertEquals(UserGallery.objects.filter(user=user.user).count(), 0)
        self.assertEquals(CommentVote.objects.filter(user=user.user, positive=True).count(), 0)
        self.assertEquals(Post.objects.filter(pk=upvoted_answer.id).first().like, 0)

        # zep 12, published contents and beta
        self.assertIsNotNone(PublishedContent.objects.filter(content__pk=published_tutorial_alone.pk).first())
        self.assertIsNotNone(PublishedContent.objects.filter(content__pk=published_tutorial_2.pk).first())
        self.assertTrue(Topic.objects.get(pk=beta_content.beta_topic.pk).is_locked)
        self.assertFalse(Topic.objects.get(pk=beta_content_2.beta_topic.pk).is_locked)

        # check API
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(AccessToken.objects.count(), 0)

        # check that the karma note and the sanction were kept
        self.assertTrue(KarmaNote.objects.filter(pk=note.pk).exists())
        self.assertTrue(Ban.objects.filter(pk=ban.pk).exists())

    def test_forgot_password(self):
        """To test nominal scenario of a lost password."""

        # Empty the test outbox
        mail.outbox = []

        result = self.client.post(
            reverse('member-forgot-password'),
            {
                'username': self.mas.user.username,
                'email': '',
            },
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 1)

        # clic on the link which has been sent in mail
        user = User.objects.get(username=self.mas.user.username)

        token = TokenForgotPassword.objects.get(user=user)
        result = self.client.get(
            settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
            follow=False)

        self.assertEqual(result.status_code, 200)

    def test_sanctions(self):
        """
        Test various sanctions.
        """

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # list of members.
        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context['members'])

        # Test: LS
        user_ls = ProfileFactory()
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
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
        self.assertEqual(ban.note, 'Texte de test pour LS')
        self.assertEquals(len(mail.outbox), 1)

        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEquals(nb_users + 1, len(result.context['members']))  # LS guy still shows up, good

        # Test: Un-LS
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
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
        self.assertEqual(ban.note, 'Texte de test pour un-LS')
        self.assertEquals(len(mail.outbox), 2)

        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEquals(nb_users + 1, len(result.context['members']))  # LS guy still shows up, good

        # Test: LS temp
        user_ls_temp = ProfileFactory()
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
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
        self.assertEqual(ban.note, u'Texte de test pour LS TEMP')
        self.assertEquals(len(mail.outbox), 3)

        # reset nb_users
        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        nb_users = len(result.context['members'])

        # Test: BAN
        user_ban = ProfileFactory()
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
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
        self.assertEqual(ban.note, u'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 4)

        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEquals(nb_users, len(result.context['members']))  # Banned guy doesn't show up, good

        # Test: un-BAN
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
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
        self.assertEqual(ban.note, u'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 5)

        result = self.client.get(reverse('member-list'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEquals(nb_users + 1, len(result.context['members']))  # UnBanned guy shows up, good

        # Test: BAN temp
        user_ban_temp = ProfileFactory()
        result = self.client.post(
            reverse('member-modify-profile',
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
        self.assertEqual(ban.note, u'Texte de test pour BAN TEMP')
        self.assertEquals(len(mail.outbox), 6)

    def test_sanctions_with_not_staff_user(self):
        user = ProfileFactory().user

        # we need staff right for update the sanction of an user, so a member who is not staff can't access to the page
        self.client.logout()
        self.client.login(username=user.username, password='hostel77')

        # Test: LS
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
                    'user_pk': self.staff.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)

        self.assertEqual(result.status_code, 403)

        # if the user is staff, he can update the sanction of an user
        self.client.logout()
        self.client.login(username=self.staff.username, password='hostel77')

        # Test: LS
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
                    'user_pk': user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)

        self.assertEqual(result.status_code, 302)

    def test_failed_bot_sanctions(self):

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        bot_profile = ProfileFactory()
        bot_profile.user.groups.add(self.bot)
        bot_profile.user.save()

        # Test: LS
        result = self.client.post(
            reverse(
                'member-modify-profile', kwargs={
                    'user_pk': bot_profile.user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)
        user = Profile.objects.get(id=bot_profile.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 403)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)

    def test_nonascii(self):
        user = NonAsciiProfileFactory()
        result = self.client.get(reverse('member-login') + '?next=' +
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
        group = Group.objects.create(name='DummyGroup_1')
        groupbis = Group.objects.create(name='DummyGroup_2')

        # create Forums, Posts and subscribe member to them.
        category1 = CategoryFactory(position=1)
        forum1 = ForumFactory(
            category=category1,
            position_in_category=1)
        forum1.groups.add(group)
        forum1.save()
        forum2 = ForumFactory(
            category=category1,
            position_in_category=2)
        forum2.groups.add(groupbis)
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
            reverse('member-settings-promote',
                    kwargs={'user_pk': tester.user.id}), follow=False)
        self.assertEqual(result.status_code, 200)

        # give groups thanks to staff (but account still not activated)
        result = self.client.post(
            reverse('member-settings-promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id, groupbis.id],
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 2)
        self.assertFalse(tester.user.is_active)

        # Now our tester is going to follow one post in every forum (3)
        TopicAnswerSubscription.objects.toggle_follow(topic1, tester.user)
        TopicAnswerSubscription.objects.toggle_follow(topic2, tester.user)
        TopicAnswerSubscription.objects.toggle_follow(topic3, tester.user)

        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 3)

        # retract all right, keep one group only and activate account
        result = self.client.post(
            reverse('member-settings-promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id],
                'activation': 'on'
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 1)
        self.assertTrue(tester.user.is_active)
        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 2)

        # no groups specified
        result = self.client.post(
            reverse('member-settings-promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'activation': 'on'
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh
        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(tester.user)), 1)

        # Finally, check that user can connect and can not access the interface
        login_check = self.client.login(
            username=tester.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member-settings-promote',
                    kwargs={'user_pk': staff.user.id}),
            {
                'activation': 'on'
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
            reverse('member-login'),
            {'username': tester.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # Check that the filter can't be access from normal user
        result = self.client.post(
            reverse('member-from-ip',
                    kwargs={'ip_address': tester.last_ip_address}),
            {}, follow=False)
        self.assertEqual(result.status_code, 403)

        # log the staff user
        result = self.client.post(
            reverse('member-login'),
            {'username': staff.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # test that we retrieve correctly the 2 members (staff + user) from this ip
        result = self.client.post(
            reverse('member-from-ip',
                    kwargs={'ip_address': staff.last_ip_address}),
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
            reverse('member-login'),
            {'username': tester.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that user can't use this feature
        result = self.client.post(reverse('member-modify-karma'), follow=False)
        self.assertEqual(result.status_code, 403)

        # login as staff
        result = self.client.post(
            reverse('member-login'),
            {'username': staff.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # try to give a few bad points to the tester
        result = self.client.post(
            reverse('member-modify-karma'),
            {'profile_pk': tester.pk,
             'note': 'Bad tester is bad !',
             'karma': '-50'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -50)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 1)

        # Now give a few good points
        result = self.client.post(
            reverse('member-modify-karma'),
            {'profile_pk': tester.pk,
             'note': 'Good tester is good !',
             'karma': '10'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 2)

        # Now access some unknow user
        result = self.client.post(
            reverse('member-modify-karma'),
            {'profile_pk': 9999,
             'note': 'Good tester is good !',
             'karma': '10'},
            follow=False)
        self.assertEqual(result.status_code, 404)

        # Now give unknow point
        result = self.client.post(
            reverse('member-modify-karma'),
            {'profile_pk': tester.pk,
             'note': 'Good tester is good !',
             'karma': ''},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 3)

        # Now give no point at all
        result = self.client.post(
            reverse('member-modify-karma'),
            {'profile_pk': tester.pk,
             'note': 'Good tester is good !'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 4)

        # Now access without post
        result = self.client.get(reverse('member-modify-karma'), follow=False)
        self.assertEqual(result.status_code, 405)

    def test_karma_and_pseudo_change(self):
        """
        To test that a karma note is added when a member change its pseudo
        """
        tester = ProfileFactory()
        old_pseudo = tester.user.username
        self.client.login(username=tester.user.username, password='hostel77')
        data = {
            'username': 'dummy',
            'email': tester.user.email
        }
        result = self.client.post(reverse('update-username-email-member'), data, follow=False)

        self.assertEqual(result.status_code, 302)
        notes = KarmaNote.objects.filter(user=tester.user).all()
        self.assertEqual(len(notes), 1)
        self.assertTrue(old_pseudo in notes[0].note and 'dummy' in notes[0].note)

    def test_ban_member_is_not_contactable(self):
        """
        When a member is ban, we hide the button to send a PM.
        """
        user_ban = ProfileFactory()
        user_ban.can_read = False
        user_ban.can_write = False
        user_ban.save()
        user_1 = ProfileFactory()
        user_2 = ProfileFactory()

        phrase = 'Envoyer un message privé'

        result = self.client.get(reverse('member-detail', args=[user_1.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        result = self.client.get(reverse('member-detail', args=[user_ban.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        self.assertTrue(self.client.login(username=user_2.user.username, password='hostel77'))
        result = self.client.get(reverse('member-detail', args=[user_1.user.username]), follow=False)
        self.client.logout()
        self.assertContains(result, phrase)

        self.assertTrue(self.client.login(username=user_2.user.username, password='hostel77'))
        result = self.client.get(reverse('member-detail', args=[user_ban.user.username]), follow=False)
        self.client.logout()
        self.assertNotContains(result, phrase)

        self.assertTrue(self.client.login(username=user_1.user.username, password='hostel77'))
        result = self.client.get(reverse('member-detail', args=[user_1.user.username]), follow=False)
        self.client.logout()
        self.assertNotContains(result, phrase)

    def test_github_token(self):
        user = ProfileFactory()
        dev = DevProfileFactory()

        # test that github settings are only availables for dev
        self.client.login(username=user.user.username, password='hostel77')
        result = self.client.get(reverse('update-github'), follow=False)
        self.assertEqual(result.status_code, 403)
        result = self.client.post(reverse('remove-github'), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.logout()

        # now, test the form
        self.client.login(username=dev.user.username, password='hostel77')
        result = self.client.get(reverse('update-github'), follow=False)
        self.assertEqual(result.status_code, 200)
        result = self.client.post(reverse('update-github'), {
            'github_token': 'test',
        }, follow=False)
        self.assertEqual(result.status_code, 302)

        # refresh
        dev = Profile.objects.get(pk=dev.pk)
        self.assertEqual(dev.github_token, 'test')

        # test the option to remove the token
        result = self.client.post(reverse('remove-github'), follow=False)
        self.assertEqual(result.status_code, 302)

        # refresh
        dev = Profile.objects.get(pk=dev.pk)
        self.assertEqual(dev.github_token, '')

    def test_markdown_help_settings(self):
        user = ProfileFactory().user

        # login and check that the Markdown help is displayed
        self.client.login(username=user.username, password='hostel77')
        result = self.client.get(reverse('pages-index'), follow=False)
        self.assertContains(result, 'data-show-markdown-help="true"')

        # disable Markdown help
        user.profile.show_markdown_help = False
        user.profile.save()
        result = self.client.get(reverse('pages-index'), follow=False)
        self.assertContains(result, 'data-show-markdown-help="false"')

    def test_new_provider_with_new_account(self):
        new_providers_count = NewEmailProvider.objects.count()

        # register a new user
        self.client.post(reverse('register-member'), {
            'username': 'new',
            'password': 'hostel77',
            'password_confirm': 'hostel77',
            'email': 'test@unknown-provider-register.com',
        }, follow=False)

        user = User.objects.get(username='new')
        token = TokenRegister.objects.get(user=user)
        self.client.get(token.get_absolute_url(), follow=False)

        # A new provider object should have been created
        self.assertEqual(new_providers_count + 1, NewEmailProvider.objects.count())

    def test_new_provider_with_email_edit(self):
        new_providers_count = NewEmailProvider.objects.count()
        user = ProfileFactory().user
        self.client.login(username=user.username, password='hostel77')
        # Edit the email with an unknown provider
        self.client.post(reverse('update-username-email-member'), {
            'username': user.username,
            'email': 'test@unknown-provider-edit.com'
        }, follow=False)
        # A new provider object should have been created
        self.assertEqual(new_providers_count + 1, NewEmailProvider.objects.count())

    def test_new_providers_list(self):
        # create a new provider
        user = ProfileFactory().user
        provider = NewEmailProvider.objects.create(use='NEW_ACCOUNT', user=user,
                                                   provider='test.com')
        # check that the list is not available for a non-staff member
        self.client.logout()
        result = self.client.get(reverse('new-email-providers'), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.login(username=user.username, password='hostel77')
        result = self.client.get(reverse('new-email-providers'), follow=False)
        self.assertEqual(result.status_code, 403)
        # and that it contains the provider we created
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.get(reverse('new-email-providers'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertIn(provider, result.context['providers'])

    def test_check_new_provider(self):
        # create two new providers
        user = ProfileFactory().user
        provider1 = NewEmailProvider.objects.create(use='NEW_ACCOUNT', user=user,
                                                    provider='test1.com')
        provider2 = NewEmailProvider.objects.create(use='EMAIl_EDIT', user=user,
                                                    provider='test2.com')
        # check that this option is only available for a staff member
        self.client.login(username=user.username, password='hostel77')
        result = self.client.post(reverse('check-new-email-provider', args=[provider1.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        # test approval
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(reverse('check-new-email-provider', args=[provider1.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(NewEmailProvider.objects.filter(pk=provider1.pk).exists())
        self.assertFalse(BannedEmailProvider.objects.filter(provider=provider1.provider).exists())
        # test ban
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(reverse('check-new-email-provider', args=[provider2.pk]),
                                  {'ban': 'on'}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(NewEmailProvider.objects.filter(pk=provider2.pk).exists())
        self.assertTrue(BannedEmailProvider.objects.filter(provider=provider2.provider).exists())

    def test_banned_providers_list(self):
        user = ProfileFactory().user
        # create a banned provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider='test.com')
        # check that the list is not available for a non-staff member
        self.client.logout()
        result = self.client.get(reverse('banned-email-providers'), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.login(username=user.username, password='hostel77')
        result = self.client.get(reverse('banned-email-providers'), follow=False)
        self.assertEqual(result.status_code, 403)
        # and that it contains the provider we created
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.get(reverse('banned-email-providers'), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertIn(provider, result.context['providers'])

    def test_add_banned_provider(self):
        # test that this page is only available for staff
        user = ProfileFactory().user
        self.client.logout()
        result = self.client.get(reverse('add-banned-email-provider'), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.login(username=user.username, password='hostel77')
        result = self.client.get(reverse('add-banned-email-provider'), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.get(reverse('add-banned-email-provider'), follow=False)
        self.assertEqual(result.status_code, 200)

        # add a provider
        result = self.client.post(reverse('add-banned-email-provider'),
                                  {'provider': 'new-provider.com'}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertTrue(BannedEmailProvider.objects.filter(provider='new-provider.com').exists())

        # check that it cannot be added again
        result = self.client.post(reverse('add-banned-email-provider'),
                                  {'provider': 'new-provider.com'}, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(1, BannedEmailProvider.objects.filter(provider='new-provider.com').count())

    def test_members_with_provider(self):
        # create two members with the same provider
        member1 = ProfileFactory().user
        member2 = ProfileFactory().user
        member1.email = 'test1@test-members.com'
        member1.save()
        member2.email = 'test2@test-members.com'
        member2.save()
        # ban this provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider='test-members.com')
        # check that this page is only available for staff
        self.client.logout()
        result = self.client.get(reverse('members-with-provider', args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.client.login(username=member1.username, password='hostel77')
        result = self.client.get(reverse('members-with-provider', args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.get(reverse('members-with-provider', args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 200)
        # check that it contains the two members
        self.assertIn(member1.profile, result.context['members'])
        self.assertIn(member2.profile, result.context['members'])

    def test_remove_banned_provider(self):
        user = ProfileFactory().user
        # add a banned provider
        provider = BannedEmailProvider.objects.create(moderator=self.staff, provider='test-remove.com')
        # check that this option is only available for a staff member
        self.client.login(username=user.username, password='hostel77')
        result = self.client.post(reverse('check-new-email-provider', args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 403)
        # test that it removes the provider
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(reverse('remove-banned-email-provider', args=[provider.pk]), follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(BannedEmailProvider.objects.filter(pk=provider.pk).exists())

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
