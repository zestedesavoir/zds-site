import logging
from datetime import datetime
import os
from django.conf import settings
from .spam_training import count_vect, tfidf_transformer, clf
from django.utils.translation import gettext_lazy as _
from zds.utils.models import Alert
from zds.member.models import Profile
from django.contrib.auth.models import User
import factory
from factory.fuzzy import FuzzyText


class SpamDetector:

    reported_users_file = "reported_users.txt"
    reported_users = []

    def __init__(self):
        self.logger = logging.getLogger("zds.spam")
        self.logger.setLevel(logging.ERROR)

        self.load_reported_users()

        # TODO: Delete this logging stuff
        for user in self.reported_users:
            self.logger.info(f"User {user} already reported")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(current_dir, "spam_detector.log")

    def check_profile(self, profile):
        """
        Check if a profile is a spammer
        """
        biography = profile.biography

        if profile.user.username not in self.reported_users:
            if not biography:
                self.logger.info("∅  %s has no biography" % profile.user.username)
                return False

            if self.check(biography) == 0:
                self.logger.info("✘  %s's biography looks like spam" % profile.user.username)
                if self.send_alert(None, profile.user.username):
                    self.reported_users.append(profile.user.username)
                    self.save_reported_users()
            else:
                self.logger.info("✔️  %s's biography doesn't look like spam" % profile.user.username)
        else:
            self.logger.info("✘  %s has already been reported as potential spam" % profile.user.username)

        self.logger.info(f"Profile checked: {profile.user.username}\n" f"Biography: {profile.biography}\n" f"{'='*50}")

    def save_reported_users(self):
        with open(self.reported_users_file, "w") as f:
            f.write("\n".join(self.reported_users))

    def load_reported_users(self):
        try:
            with open(self.reported_users_file) as f:
                self.reported_users = f.read().split("\n")
        except FileNotFoundError:
            self.reported_users = []

    def check(self, biography):
        X_new_counts = count_vect.transform([biography])
        X_new_tfidf = tfidf_transformer.transform(X_new_counts)
        return clf.predict(X_new_tfidf)[0]

    def send_alert(self, website, username):
        """
        Create an alert for a spam-suspect user
        """
        try:
            profile = Profile.objects.get(user__username=username)

            message = _("Spam")

            Alert.objects.create(
                author=User.objects.get(username="bot"),
                profile=profile,
                scope="PROFILE",
                text=message,
                pubdate=datetime.now(),
            )

            self.logger.info(f"Spam-Alert for {username} created")
            return True

        except Exception as e:
            self.logger.error(f"Error on creation of spam report for {username}: {str(e)}")
            return False
