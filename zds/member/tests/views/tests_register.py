import os
from datetime import datetime
from smtplib import SMTPException
from unittest.mock import Mock

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from oauth2_provider.models import AccessToken, Application

from zds.forum.models import Post, Topic
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.gallery.models import Gallery, UserGallery
from zds.gallery.tests.factories import GalleryFactory, UserGalleryFactory
from zds.member.models import Ban, KarmaNote, NewEmailProvider, TokenRegister
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import PrivatePost, PrivateTopic
from zds.mp.tests.factories import PrivatePostFactory, PrivateTopicFactory
from zds.tutorialv2.models.database import PublishableContent, PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import BetaContentFactory, PublishableContentFactory, PublishedContentFactory
from zds.utils.models import CommentVote


@override_for_contents()
class TestRegister(TutorialTestMixin, TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        self.category1 = ForumCategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.staff = StaffProfileFactory().user

        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_register(self):
        """
        To test user registration.
        """

        # register a new user.
        result = self.client.post(
            reverse("register-member"),
            {
                "username": "firm1",
                "password": "flavour",
                "password_confirm": "flavour",
                "email": "firm1@zestedesavoir.com",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # check email has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # check if the new user is well inactive.
        user = User.objects.get(username="firm1")
        self.assertFalse(user.is_active)

        # make a request on the link which has been sent in mail to
        # confirm the registration.
        token = TokenRegister.objects.get(user=user)
        result = self.client.get(settings.ZDS_APP["site"]["url"] + token.get_absolute_url(), follow=False)
        self.assertEqual(result.status_code, 200)

        # check a new email hasn't been sent at the new user.
        self.assertEqual(len(mail.outbox), 1)

        # check if the new user is active.
        self.assertTrue(User.objects.get(username="firm1").is_active)

    def test_unauthenticated_user_cant_unregister(self):
        """An unauthenticated user shall not be able to unregister."""
        self.client.logout()
        result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
        self.assertEqual(result.status_code, 302)

    def test_unregister_base_case(self):
        """
        An authenticated user shall be able to unregister.
        Base case with no content, API keys, etc. attached to the user.
        """
        user = ProfileFactory()
        self.client.force_login(user.user)
        result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 0)

    def test_unregister_with_attached_artefacts(self):
        """
        Test unregistering a user with many contents, PM, API keys...
        """

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
        published_tutorial_alone = PublishedContentFactory(type="TUTORIAL")
        published_tutorial_alone.authors.add(user.user)
        published_tutorial_alone.save()
        # second case : a published tutorial with two authors
        published_tutorial_2 = PublishedContentFactory(type="TUTORIAL")
        published_tutorial_2.authors.add(user.user)
        published_tutorial_2.authors.add(user2.user)
        published_tutorial_2.save()
        # third case : a private tutorial with only one author
        writing_tutorial_alone = PublishableContentFactory(type="TUTORIAL")
        writing_tutorial_alone.authors.add(user.user)
        writing_tutorial_alone.save()
        writing_tutorial_alone_galler_path = writing_tutorial_alone.gallery.get_gallery_path()
        # fourth case : a private tutorial with at least two authors
        writing_tutorial_2 = PublishableContentFactory(type="TUTORIAL")
        writing_tutorial_2.authors.add(user.user)
        writing_tutorial_2.authors.add(user2.user)
        writing_tutorial_2.save()
        self.client.force_login(self.staff)
        # same thing for articles
        published_article_alone = PublishedContentFactory(type="ARTICLE")
        published_article_alone.authors.add(user.user)
        published_article_alone.save()
        published_article_2 = PublishedContentFactory(type="ARTICLE")
        published_article_2.authors.add(user.user)
        published_article_2.authors.add(user2.user)
        published_article_2.save()
        writing_article_alone = PublishableContentFactory(type="ARTICLE")
        writing_article_alone.authors.add(user.user)
        writing_article_alone.save()
        writing_article_2 = PublishableContentFactory(type="ARTICLE")
        writing_article_2.authors.add(user.user)
        writing_article_2.authors.add(user2.user)
        writing_article_2.save()
        # beta content
        beta_forum = ForumFactory(category=ForumCategoryFactory())
        beta_content = BetaContentFactory(author_list=[user.user], forum=beta_forum)
        beta_content_2 = BetaContentFactory(author_list=[user.user, user2.user], forum=beta_forum)
        # about posts and topics
        authored_topic = TopicFactory(author=user.user, forum=self.forum11, solved_by=user.user)
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
        api_application.client_id = "foobar"
        api_application.user = user.user
        api_application.client_type = "confidential"
        api_application.authorization_grant_type = "password"
        api_application.client_secret = "42"
        api_application.save()
        token = AccessToken()
        token.user = user.user
        token.token = "r@d0m"
        token.application = api_application
        token.expires = datetime.now()
        token.save()
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(AccessToken.objects.count(), 1)

        # add a karma note and a sanction with this user
        note = KarmaNote(moderator=user.user, user=user2.user, note="Good!", karma=5)
        note.save()
        ban = Ban(moderator=user.user, user=user2.user, type="Ban définitif", note="Test")
        ban.save()

        # login and unregister:
        self.client.force_login(user.user)
        result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
        self.assertEqual(result.status_code, 302)

        # check that the bot have taken authorship of tutorial:
        self.assertEqual(published_tutorial_alone.authors.count(), 1)
        self.assertEqual(
            published_tutorial_alone.authors.first().username, settings.ZDS_APP["member"]["external_account"]
        )
        self.assertFalse(os.path.exists(writing_tutorial_alone_galler_path))
        self.assertEqual(published_tutorial_2.authors.count(), 1)
        self.assertEqual(
            published_tutorial_2.authors.filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0
        )

        # check that published tutorials remain published and accessible
        self.assertIsNotNone(published_tutorial_2.public_version.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_2.public_version.get_prod_path()))
        self.assertIsNotNone(published_tutorial_alone.public_version.get_prod_path())
        self.assertTrue(os.path.exists(published_tutorial_alone.public_version.get_prod_path()))
        self.assertEqual(
            self.client.get(
                reverse("tutorial:view", args=[published_tutorial_alone.pk, published_tutorial_alone.slug]),
                follow=False,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("tutorial:view", args=[published_tutorial_2.pk, published_tutorial_2.slug]), follow=False
            ).status_code,
            200,
        )

        # test that published articles remain accessible
        self.assertTrue(os.path.exists(published_article_alone.public_version.get_prod_path()))
        self.assertEqual(
            self.client.get(
                reverse("article:view", args=[published_article_alone.pk, published_article_alone.slug]), follow=True
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("article:view", args=[published_article_2.pk, published_article_2.slug]), follow=True
            ).status_code,
            200,
        )

        # check that the tutorial for which the author was alone does not exists anymore
        self.assertEqual(PublishableContent.objects.filter(pk=writing_tutorial_alone.pk).count(), 0)
        self.assertFalse(os.path.exists(writing_tutorial_alone.get_repo_path()))

        # check that bot haven't take the authorship of the tuto with more than one author
        self.assertEqual(writing_tutorial_2.authors.count(), 1)
        self.assertEqual(
            writing_tutorial_2.authors.filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0
        )

        # authorship for the article for which user was the only author
        self.assertEqual(published_article_alone.authors.count(), 1)
        self.assertEqual(
            published_article_alone.authors.first().username, settings.ZDS_APP["member"]["external_account"]
        )
        self.assertEqual(published_article_2.authors.count(), 1)

        self.assertEqual(PublishableContent.objects.filter(pk=writing_article_alone.pk).count(), 0)
        self.assertFalse(os.path.exists(writing_article_alone.get_repo_path()))

        # not bot if another author:
        self.assertEqual(
            published_article_2.authors.filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0
        )
        self.assertEqual(writing_article_2.authors.count(), 1)
        self.assertEqual(
            writing_article_2.authors.filter(username=settings.ZDS_APP["member"]["external_account"]).count(), 0
        )

        # topics, gallery and PMs:
        self.assertEqual(Topic.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Topic.objects.filter(solved_by=user.user).count(), 0)
        self.assertEqual(Topic.objects.filter(solved_by=self.anonymous).count(), 1)
        self.assertEqual(Post.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(Post.objects.filter(editor__username=user.user.username).count(), 0)
        self.assertEqual(PrivatePost.objects.filter(author__username=user.user.username).count(), 0)
        self.assertEqual(PrivateTopic.objects.filter(author__username=user.user.username).count(), 0)

        self.assertIsNotNone(Topic.objects.get(pk=authored_topic.pk))
        self.assertIsNotNone(PrivateTopic.objects.get(pk=private_topic.pk))
        self.assertIsNotNone(Gallery.objects.get(pk=alone_gallery.pk))
        self.assertEqual(alone_gallery.get_linked_users().count(), 1)
        self.assertEqual(shared_gallery.get_linked_users().count(), 1)
        self.assertEqual(UserGallery.objects.filter(user=user.user).count(), 0)
        self.assertEqual(CommentVote.objects.filter(user=user.user, positive=True).count(), 0)
        self.assertEqual(Post.objects.filter(pk=upvoted_answer.id).first().like, 0)

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

    def test_register_with_not_allowed_chars(self):
        """
        Test register account with not allowed chars
        :return:
        """
        users = [
            # empty username
            {"username": "", "password": "flavour", "password_confirm": "flavour", "email": "firm1@zestedesavoir.com"},
            # space after username
            {
                "username": "firm1 ",
                "password": "flavour",
                "password_confirm": "flavour",
                "email": "firm1@zestedesavoir.com",
            },
            # space before username
            {
                "username": " firm1",
                "password": "flavour",
                "password_confirm": "flavour",
                "email": "firm1@zestedesavoir.com",
            },
            # username with utf8mb4 chars
            {
                "username": " firm1",
                "password": "flavour",
                "password_confirm": "flavour",
                "email": "firm1@zestedesavoir.com",
            },
        ]

        for user in users:
            result = self.client.post(reverse("register-member"), user, follow=False)
            self.assertEqual(result.status_code, 200)
            # check any email has been sent.
            self.assertEqual(len(mail.outbox), 0)
            # user doesn't exist
            self.assertEqual(User.objects.filter(username=user["username"]).count(), 0)

    def test_new_provider_with_new_account(self):
        new_providers_count = NewEmailProvider.objects.count()

        # register a new user
        self.client.post(
            reverse("register-member"),
            {
                "username": "new",
                "password": "hostel77",
                "password_confirm": "hostel77",
                "email": "test@unknown-provider-register.com",
            },
            follow=False,
        )

        user = User.objects.get(username="new")
        token = TokenRegister.objects.get(user=user)
        self.client.get(token.get_absolute_url(), follow=False)

        # A new provider object should have been created
        self.assertEqual(new_providers_count + 1, NewEmailProvider.objects.count())


mail_backend = Mock()


class FakeBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        return mail_backend.send_messages(email_messages)


@override_settings(EMAIL_BACKEND="zds.member.tests.views.tests_register.FakeBackend")
class RegisterTest(TestCase):
    def test_exception_on_mail(self):
        def send_messages(messages):
            print("message sent")
            raise SMTPException(messages)

        mail_backend.send_messages = send_messages

        result = self.client.post(
            reverse("register-member"),
            {
                "username": "firm1",
                "password": "flavour",
                "password_confirm": "flavour",
                "email": "firm1@zestedesavoir.com",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertIn(escape("Impossible d'envoyer l'email."), result.content.decode("utf-8"))
