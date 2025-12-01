import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from zds.antispam.spam_fields import spam_fields
from zds.antispam.spam_model_manager import SpamModelManager
from zds.utils.models import Alert


class SpamDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_manager = SpamModelManager()

    def check_text(self, text, content_type):
        """
        Check if a given text is spam for the specified content type.
        """
        if not text:
            self.logger.warning(f"Skipped spam check: Empty text for content type '{content_type}'.")
            return False

        try:
            prediction = self.model_manager.predict(content_type, [text])[0]
            if prediction == 0:  # 0 indicates spam
                self.logger.info(
                    f"✘ Spam detected for content type '{content_type}'. Text: '{text[:30]}...' (Length: {len(text)})"
                )
                return True
            else:
                self.logger.info(
                    f"✔️ No spam detected for content type '{content_type}'. Text: '{text[:30]}...' (Length: {len(text)})"
                )
                return False
        except Exception as e:
            self.logger.error(f"Error during spam detection for content type '{content_type}': {e}")
            return False

    def send_alert(self, instance, field_name):
        """
        Create an alert for a spam-suspect field with detailed context.
        """
        try:
            # Find the spam field configuration for the instance
            field_config = next(
                (
                    config
                    for config in spam_fields
                    if isinstance(instance, config["model"]) and field_name in config["fields"]
                ),
                None,
            )
            if not field_config:
                self.logger.error(f"No spam field configuration found for {type(instance).__name__}.{field_name}")
                return

            # Extract scope and instance info
            scope = field_config["scope"]
            instance_info = field_config["get_instance_info"](instance)

            # Map scope to the correct Alert model field
            scope_to_alert_kwargs = {
                "PROFILE": "profile",
                "FORUM": "comment",
                "CONTENT": "content",
            }

            if scope not in scope_to_alert_kwargs:
                self.logger.error(f"Unsupported scope '{scope}' for alert creation.")
                return

            alert_kwargs = {
                "author": User.objects.get(username="antispam"),
                "scope": scope,
                "text": _(f"Potential spam detected in {instance_info}, field '{field_name}'."),
                "pubdate": datetime.now(),
                scope_to_alert_kwargs[scope]: instance,
            }

            # Create the alert
            Alert.objects.create(**alert_kwargs)
            self.logger.info(f"Spam-Alert for {instance_info}, field '{field_name}' created.")
        except User.DoesNotExist:
            self.logger.error("The 'antispam' user does not exist. Please create this user.")
        except Exception as e:
            self.logger.error(f"Failed to create spam alert: {e}")
