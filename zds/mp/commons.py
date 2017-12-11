from datetime import datetime

from zds.utils.templatetags.emarkdown import emarkdown


class LeavePrivateTopic(object):
    """
    Leave a private topic.
    """

    def perform_destroy(self, instance):
        if instance.participants.count() == 0:
            instance.delete()
        elif self.get_current_user().pk == instance.author.pk:
            move = instance.participants.first()
            instance.author = move
            instance.participants.remove(move)
            instance.save()
        else:
            instance.participants.remove(self.get_current_user())
            instance.save()

    def get_current_user(self):
        raise NotImplementedError('`get_current_user()` must be implemented.')


class UpdatePrivatePost(object):
    """
    Updates a private topic.
    """

    def perform_update(self, instance, data, hat=None):
        instance.hat = hat
        instance.text = data.get('text')
        instance.text_html = emarkdown(data.get('text'))
        instance.update = datetime.now()
        instance.save()
        return instance
