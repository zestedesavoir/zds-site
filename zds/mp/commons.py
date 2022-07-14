from datetime import datetime

from zds.utils.templatetags.emarkdown import emarkdown


class LeavePrivateTopic:
    """
    Leave a private topic.
    """

    def perform_destroy(self, topic):
        if topic.one_participant_remaining():
            topic.delete()
        else:
            topic.remove_participant(self.get_current_user())
            topic.save()

    def get_current_user(self):
        raise NotImplementedError("`get_current_user()` must be implemented.")


class UpdatePrivatePost:
    """
    Updates a private topic.
    """

    def perform_update(self, instance, data, hat=None):
        instance.hat = hat
        instance.text = data.get("text")
        instance.text_html = emarkdown(data.get("text"))
        instance.update = datetime.now()
        instance.save()
        return instance
