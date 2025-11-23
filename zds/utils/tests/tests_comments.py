from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from zds.forum.tests.factories import PostFactory, create_category_and_forum, create_topic_in_forum
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.member.utils import get_bot_account
from zds.tutorialv2.models import CONTENT_TYPES
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import PublishedContentFactory
from zds.utils.models import Alert


class PotentialSpamTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.client_api = APIClient()

        # We need a bot for test_mark_as_potential_spam.
        settings.ZDS_APP["member"]["bot_account"] = ProfileFactory().user.username

        # For content-based tests
        self.overridden_zds_app = settings.ZDS_APP
        settings.ZDS_APP["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
        settings.ZDS_APP["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def logout(self):
        self.client.logout()
        self.client_api.logout()

    def login(self, profile):
        self.logout()
        self.client.force_login(profile.user)
        self.client_api.force_login(profile.user)

    def test_mark_as_potential_spam_forum(self):
        author = ProfileFactory()
        staff = StaffProfileFactory()

        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, author)
        PostFactory(topic=topic, author=author.user, position=2)

        comment = topic.last_message

        self.common_test_mark_as_potential_spam(
            url_comments_list=reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]),
            url_comment_edit=reverse("forum:post-edit") + f"?message={comment.pk}",
            comment=comment,
            author=author,
            staff=staff,
        )

    def test_mark_as_potential_spam_content(self):
        for content_type in CONTENT_TYPES:
            self.common_test_mark_as_potential_spam_content(content_type["name"])

    def common_test_mark_as_potential_spam_content(self, content_type):
        content_author = ProfileFactory()
        comment_author = ProfileFactory()
        staff = StaffProfileFactory()

        content: PublishableContent = PublishedContentFactory(author_list=[content_author.user], type=content_type)

        self.login(comment_author)
        self.client.post(
            reverse("content:add-reaction") + f"?pk={content.pk}",
            {"text": "Pi is not so humble", "last_note": "0"},
            follow=True,
        )
        content.refresh_from_db()
        reaction = content.last_note

        self.common_test_mark_as_potential_spam(
            url_comments_list=content.get_absolute_url_online(),
            url_comment_edit=reverse("content:update-reaction") + f"?message={reaction.pk}&pk={content.pk}",
            comment=reaction,
            author=comment_author,
            staff=staff,
        )

    def common_test_mark_as_potential_spam(self, url_comments_list, url_comment_edit, comment, author, staff):
        bot = get_bot_account()

        potential_spam_class_not_there_if_not_staff = "potential-spam"
        potential_spam_classes_if_hidden = 'class="message-potential-spam alert ico-after hidden"'
        potential_spam_classes_if_visible = 'class="message-potential-spam alert ico-after "'
        alert_text = "Ce message, soupçonné d'être un spam, a été modifié."

        # unauthenticated, no potential spam, no message
        self.logout()
        response = self.client.get(url_comments_list)
        self.assertNotContains(response, potential_spam_class_not_there_if_not_staff)

        # authenticated, no potential spam, no message
        self.login(staff)
        response = self.client.get(url_comments_list)
        self.assertContains(response, potential_spam_classes_if_hidden)

        # unauthenticated, cannot mark a message as potential spam
        self.logout()
        response = self.client_api.put(
            reverse("api:utils:update-comment-potential-spam", args=[comment.pk]), {"is_potential_spam": True}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # authenticated as non-staff, cannot mark a message as potential spam
        self.login(author)
        response = self.client_api.put(
            reverse("api:utils:update-comment-potential-spam", args=[comment.pk]), {"is_potential_spam": True}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # authenticated as non-staff, if we edit the message, there is no alert
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (1)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # authenticated as staff, if we edit the message, there is no alert
        self.login(staff)
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (2)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # authenticated as staff, can mark a message as potential spam
        response = self.client_api.put(
            reverse("api:utils:update-comment-potential-spam", args=[comment.pk]), {"is_potential_spam": True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"is_potential_spam": True})

        # ok so now we have a message marked as potential spam

        # authenticated as staff, can see the message marked as potential spam
        response = self.client.get(url_comments_list)
        self.assertContains(response, potential_spam_classes_if_visible)

        # authenticated as staff, if we edit the message, there is no alert
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (21)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # authenticated as non-staff, if we edit the message, there is an alert
        self.login(author)
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (22)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 1)

        # authenticated as non-staff, if we edit again the message, there is still one alert (we don't stack them up)
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (23)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 1)

        # let's assume the alert was solved
        for alert in Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False):
            alert.solve(staff.user)

        # authenticated as non-staff, if we edit but the text doesn't actually change, there is no alert
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (23)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # ...but as the other alert was solved, if we now edit the message for real, there is a new alert
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (24)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 1)

        # ... and there are two alerts in total, including the solved one
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text)), 2)

        # let's unmark the message, it's no longer some spam
        self.login(staff)
        response = self.client_api.put(
            reverse("api:utils:update-comment-potential-spam", args=[comment.pk]), {"is_potential_spam": False}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"is_potential_spam": False})

        # oh, and the alert was solved in the meantime
        for alert in Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False):
            alert.solve(staff.user)

        # if the staff edits the message, there is no alert
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (25)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # if the author edits the message, there is no alert either
        self.login(author)
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (26)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)

        # Now we test a tricky scenario:
        # 1. a user creates a message;
        # 2. the same user edits the message;
        # 3. a staff member marks the message as potential spam.
        # No alert should be sent.
        # The message was already modified by its author just before, so we'll start at the third step.

        self.login(staff)
        response = self.client_api.put(
            reverse("api:utils:update-comment-potential-spam", args=[comment.pk]), {"is_potential_spam": True}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"is_potential_spam": True})

        # Still logged in as staff, we edit the message. There is no alert.
        response = self.client.post(url_comment_edit, {"text": "Argh du spam (27)"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(len(Alert.objects.filter(author=bot, comment=comment, text=alert_text, solved=False)), 0)
