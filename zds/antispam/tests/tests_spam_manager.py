import os
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from zds.antispam.spam_model_manager import SpamModelManager


class SpamModelManagerTestCase(TestCase):
    def setUp(self):
        """Set up test users and spam manager."""
        self.model_manager = SpamModelManager()
        self.content_type = "PROFILE"
        self.model_file = os.path.join("antispam-data", "profile_spam_model.pkl")
        # Patch the model_mapping to use our test path
        self.model_manager.model_mapping = {
            "PROFILE": "profile_spam_model.pkl",
            "FORUM": "forum_spam_model.pkl",
            "CONTENT": "content_spam_model.pkl",
        }

    @patch("zds.antispam.spam_model_manager.joblib.dump")
    @patch("zds.antispam.spam_model_manager.os.makedirs")
    def test_save_model(self, mock_makedirs, mock_dump):
        """Test that the model is saved correctly."""
        # Mock prepare_training_data to return balanced classes (0 and 1)
        with patch(
            "zds.antispam.spam_model_manager.SpamModelManager.prepare_training_data",
            return_value=(["spam text", "not spam text"], [0, 1]),
        ):
            with patch("zds.antispam.spam_model_manager.settings.ANTISPAM_PATH", "antispam-data"):
                self.model_manager.train(self.content_type)
        mock_dump.assert_called_once()

    @patch("zds.antispam.spam_model_manager.joblib.load")
    @patch("zds.antispam.spam_model_manager.os.path.exists", return_value=True)
    def test_load_model(self, mock_exists, mock_load):
        """Test that the model is loaded correctly if the file exists."""
        mock_load.return_value = (MagicMock(), MagicMock(), MagicMock())
        with patch("zds.antispam.spam_model_manager.settings.ANTISPAM_PATH", "antispam-data"):
            self.model_manager.load_model(self.content_type)
        mock_load.assert_called_once_with(self.model_file)
        self.assertIsNotNone(self.model_manager.models[self.content_type][0])
        self.assertIsNotNone(self.model_manager.models[self.content_type][1])
        self.assertIsNotNone(self.model_manager.models[self.content_type][2])

    @patch("zds.antispam.spam_model_manager.os.path.exists", return_value=False)
    @patch("zds.antispam.spam_model_manager.os.makedirs")
    @patch("zds.antispam.spam_model_manager.SpamModelManager.train")
    def test_load_model_file_not_exist(self, mock_train, mock_makedirs, mock_exists):
        """Test that loading is skipped if the file does not exist."""
        with patch("zds.antispam.spam_model_manager.settings.ANTISPAM_PATH", "antispam-data"):
            with self.assertLogs("zds.antispam.spam_model_manager", level="INFO") as log:
                self.model_manager.load_model(self.content_type)
                self.assertIn(f"Model file for {self.content_type} does not exist", log.output[0])
        mock_train.assert_called_once_with(self.content_type)

    @patch("zds.antispam.spam_model_manager.CountVectorizer.fit_transform")
    @patch("zds.antispam.spam_model_manager.TfidfTransformer.fit_transform")
    @patch("zds.antispam.spam_model_manager.LinearSVC.fit")
    @patch("zds.antispam.spam_model_manager.SpamModelManager.prepare_training_data")
    def test_train_model(self, mock_prepare, mock_fit, mock_tfidf, mock_count_vect):
        """Test that the model is trained correctly."""
        # Return data with both classes (0 and 1)
        mock_prepare.return_value = (["spam text", "not spam text"], [0, 1])
        with patch("zds.antispam.spam_model_manager.settings.ANTISPAM_PATH", "antispam-data"):
            self.model_manager.train(self.content_type)
        mock_count_vect.assert_called_once()
        mock_tfidf.assert_called_once()
        mock_fit.assert_called_once()
