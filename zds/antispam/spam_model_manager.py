import logging
import os

import joblib
from django.conf import settings
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC

from zds.antispam.spam_fields import spam_fields


class SpamModelManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_mapping = {
            "PROFILE": "profile_spam_model.pkl",
            "FORUM": "forum_spam_model.pkl",
            "CONTENT": "content_spam_model.pkl",
        }
        self.models = {}

    def ensure_directory_exists(self, model_file):
        directory = os.path.dirname(model_file)
        if not directory:
            raise ValueError("The directory for the model file is not defined.")
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created directory: {directory}")

    def prepare_training_data(self, content_type):
        """
        Prepare training data for the given content type by loading data from the database.
        Dynamically adapts to the configuration in spam_fields.
        """
        field_configs = [config for config in spam_fields if config["scope"] == content_type]
        if not field_configs:
            self.logger.error(f"No spam field configuration found for content type: {content_type}")
            return [], []

        data = []
        labels = []

        for config in field_configs:
            model = config["model"]
            fields = config["fields"]

            # Query the database for all instances of the model
            instances = model.objects.all()

            for instance in instances:
                for field_name in fields:
                    field_value = getattr(instance, field_name, None)
                    if field_value:
                        data.append(field_value)
                        # Use the is_spam method to determine the label
                        labels.append(0 if instance.is_spam(field_name) else 1)

        # if there are no 1s or no 0s in the labels use synthetic data, this is only used in the creation of the test-db
        if 0 not in labels or 1 not in labels:
            self.logger.warning(
                f"Data for {content_type} is unbalanced or empty. Using synthetic data for training. \n"
            )
            self.logger.debug(f"Data: {data} \n" f"Labels: {labels}")
            data = [
                "Spam: Buy cheap products now!",
                "Spam: Click here for free money!",
                "Spam: Limited time offer!",
                "Spam: Win a lottery!",
                "Spam: Free gift card!",
                "Spam: Earn money from home!",
                "This is a legitimate message.",
                "Another non-spam message.",
                "Just a friendly reminder.",
                "This is not spam.",
                "Important update regarding your account.",
                "Meeting agenda for tomorrow.",
                "Project deadline approaching.",
            ]
            labels = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]  # 0 for spam, 1 for non-spam

        # Log the training data and labels
        self.logger.debug(f"Training data for {content_type}: {data}")
        self.logger.debug(f"Training labels for {content_type}: {labels}")

        return data, labels

    def train(self, content_type):
        """
        Train the model for the given content type and save it to a file.
        """
        self.logger.info(f"Starting training for content type: {content_type}")

        model_file = os.path.join(settings.ANTISPAM_PATH, self.model_mapping[content_type])
        self.ensure_directory_exists(model_file)

        # Prepare training data
        data, labels = self.prepare_training_data(content_type)

        # Log the data being used for training
        self.logger.info(f"Training data for {content_type}: {data}")
        self.logger.info(f"Training labels for {content_type}: {labels}")

        # Train the model
        count_vect = CountVectorizer()
        X_train_counts = count_vect.fit_transform(data)

        tfidf_transformer = TfidfTransformer()
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

        clf = LinearSVC(max_iter=5000, loss="hinge", dual="auto")
        clf.fit(X_train_tfidf, labels)

        # Save the model
        joblib.dump((clf, count_vect, tfidf_transformer), model_file)
        self.logger.info(f"Model for {content_type} saved to {model_file}")

        # Store the model in memory
        self.models[content_type] = (clf, count_vect, tfidf_transformer)

    def load_model(self, content_type):
        """
        Load the model for the given content type from a file.
        """
        model_file = os.path.join(settings.ANTISPAM_PATH, self.model_mapping[content_type])
        if os.path.exists(model_file):
            self.models[content_type] = joblib.load(model_file)
            self.logger.info(f"Model for {content_type} loaded from {model_file}")
        else:
            self.logger.warning(f"Model file for {content_type} does not exist. Training a new model.")
            self.train(content_type)

    def predict(self, content_type, texts):
        """
        Predict whether the given texts are spam or not for the specified content type.
        """
        if content_type not in self.models:
            self.load_model(content_type)

        clf, count_vect, tfidf_transformer = self.models[content_type]
        X_new_counts = count_vect.transform(texts)
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)
        return clf.predict(X_new_tfidf)
