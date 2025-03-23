from django.test import TestCase
from django.contrib.auth.models import User
from zds.member.models import Profile
from unittest.mock import patch
from zds.utils.spam_detector import SpamDetector

"""class SpamDetectorTestCase(TestCase):

    @patch('zds.utils.spam_detector.SpamDetector.send_alert')  #To avoid sending the actual alert
    def test_check_profile_no_bio(self, mock_send_alert):
        # Create a user profile
        self.user = User.objects.create_user(username="testuser1", password="password")
        self.profile = Profile.objects.create(user=self.user)

        self.spam_detector = SpamDetector()
        #User without a biography
        self.profile.biography = ""

        # Appeler la méthode qui devrait vérifier la biographie de l'utilisateur
        self.spam_detector.check_profile(self.profile)

        # Vérifier que l'alerte n'a pas été envoyée
        mock_send_alert.assert_not_called()

        # Vérifier le message de log
        with self.assertLogs(self.spam_detector.logger, level='INFO') as log:
            self.spam_detector.check_profile(self.profile)
            self.assertIn("∅  testuser has no biography", log.output)
"""


class SpamDetectorTestCase(TestCase):

    def setUp(self):
        """Set up test users and spam detector."""
        self.spam_detector = SpamDetector()
        self.bot_user = User.objects.create_user(username="bot", password="password")

        # Create test users
        self.user1 = User.objects.create_user(username="user_no_bio", password="password")
        self.profile1 = Profile.objects.create(user=self.user1, biography="")

        self.user2 = User.objects.create_user(username="user_spam", password="password")
        self.profile2 = Profile.objects.create(user=self.user2, biography="Buy cheap products now!")

        self.user3 = User.objects.create_user(username="user_clean", password="password")
        self.profile3 = Profile.objects.create(user=self.user3, biography="I love programming and open-source.")

    @patch("zds.utils.spam_detector.SpamDetector.send_alert")
    def test_check_profile_no_bio(self, mock_send_alert):
        """User with no biography should not trigger an alert."""
        self.spam_detector.check_profile(self.profile1)
        mock_send_alert.assert_not_called()
        # Assert the log message is correct
        with self.assertLogs(self.spam_detector.logger, level="INFO") as log:
            self.spam_detector.check_profile(self.profile1)
            self.assertIn("INFO:zds.spam:∅  user_no_bio has no biography", log.output)

    @patch("zds.utils.spam_detector.SpamDetector.send_alert", return_value=True)
    @patch("zds.utils.spam_training.clf.predict", return_value=[0])  # Simulate spam detection
    def test_check_profile_spam(self, mock_predict, mock_send_alert):
        """User with spam biography should trigger an alert."""
        self.spam_detector.reported_users = []  # clear the reported_users file
        with self.assertLogs(self.spam_detector.logger, level="INFO") as log:
            self.spam_detector.check_profile(self.profile2)
            mock_send_alert.assert_called_once_with(None, "user_spam")
            self.assertIn("INFO:zds.spam:✘  user_spam's biography looks like spam", log.output)

    @patch("zds.utils.spam_detector.SpamDetector.send_alert")
    @patch("zds.utils.spam_training.clf.predict", return_value=[1])  # Simulate non-spam detection
    def test_check_profile_clean(self, mock_predict, mock_send_alert):
        """User with a clean biography should not trigger an alert."""
        self.spam_detector.check_profile(self.profile3)
        mock_send_alert.assert_not_called()

        with self.assertLogs(self.spam_detector.logger, level="INFO") as log:
            self.spam_detector.check_profile(self.profile3)
            self.assertIn("INFO:zds.spam:✔️  user_clean's biography doesn't look like spam", log.output)

    def test_reported_users_persistence(self):
        """Reported users should be saved and loaded correctly."""
        self.spam_detector.reported_users.append("user_spam")
        self.spam_detector.save_reported_users()

        new_detector = SpamDetector()
        self.assertIn("user_spam", new_detector.reported_users)
        with self.assertLogs(self.spam_detector.logger, level="INFO") as log:
            self.spam_detector.check_profile(self.profile2)
            self.assertIn("INFO:zds.spam:✘  user_spam has already been reported as potential spam", log.output)

    @patch("zds.utils.spam_training.clf.predict", return_value=[0])
    def test_check_function_spam(self, mock_predict):
        """check function should correctly classify spam."""
        result = self.spam_detector.check("Buy cheap products now!")
        self.assertEqual(result, 0)

    @patch("zds.utils.spam_training.clf.predict", return_value=[1])
    def test_check_function_clean(self, mock_predict):
        """check function should correctly classify non-spam."""
        result = self.spam_detector.check("I love programming and open-source.")
        self.assertEqual(result, 1)

    @patch("zds.utils.spam_detector.SpamDetector.send_alert", return_value=True)
    def test_already_reported_user(self, mock_send_alert):
        """User already reported should not be reported again."""
        self.spam_detector.reported_users.append("user_spam")
        self.spam_detector.check_profile(self.profile2)
        mock_send_alert.assert_not_called()
