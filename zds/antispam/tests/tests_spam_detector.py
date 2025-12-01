from django.contrib.auth.models import User
from django.test import TestCase

from zds.antispam.spam_detector import SpamDetector
from zds.member.models import Profile
from zds.utils.models import Alert


class SpamDetectorTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.detector = SpamDetector()
        # train the model for the content_type "PROFILE"
        cls.detector.model_manager.train("PROFILE")
        cls.antispam_user = User.objects.create_user(username="antispam", password="pwd")

        cls.user_clean = User.objects.create_user(username="clean_user", password="pwd")
        cls.clean_profile = Profile.objects.create(user=cls.user_clean, biography="This is a legitimate message.")

        cls.user_spam = User.objects.create_user(username="spam_user", password="pwd")
        cls.spam_profile = Profile.objects.create(
            user=cls.user_spam, biography="Buy cheap sunglasses now!!! Visit our website: bdeenseirb.com"
        )

    def test_check_empty_text(self):
        self.assertFalse(self.detector.check_text("", "PROFILE"))
        self.assertFalse(self.detector.check_text(None, "PROFILE"))

    def test_clean_biography(self):
        """Test that legitimate text is not flagged as spam."""

        check = self.detector.check_text(self.clean_profile.biography, "PROFILE")
        alert_count = Alert.objects.count()
        if check:
            self.detector.send_alert(self.clean_profile, "biography")
        self.assertEqual(Alert.objects.count(), alert_count)

    def test_spammy_biography(self):
        """Test that spammy text is detected and alert is triggered."""
        self.assertTrue(self.detector.check_text(self.spam_profile.biography, "PROFILE"))

    def test_send_alert(self):
        """Test that alerts are sent properly for spam_profile."""
        alert_count = Alert.objects.count()
        self.detector.send_alert(self.spam_profile, "biography")

        self.assertEqual(Alert.objects.count(), alert_count + 1)

        alert = Alert.objects.latest("pubdate")
        self.assertEqual(alert.author.username, "antispam")
        self.assertEqual(alert.scope, "PROFILE")
        self.assertIn("biography", alert.text)
        self.assertEqual(alert.profile, self.spam_profile)
