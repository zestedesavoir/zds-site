# coding: utf-8

from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from zds.mp.models import PrivatePost, mark_read
from zds.notification.models import Notification


class Command(BaseCommand):

    help = 'Fix https://github.com/zestedesavoir/zds-site/issues/3639 (notifications not deleted on mp leave)'

    def handle(self, *args, **options):
        mp_content_type = ContentType.objects.get(model='privatepost')
        # get all mp notifications unread
        for notification in Notification.objects.filter(is_read=False, content_type=mp_content_type):
            print('notif', notification)
            topic = PrivatePost.objects.get(pk=notification.object_id).privatetopic
            user = notification.sender
            if not topic.is_participant(user):
                mark_read(topic, user)
                self.stdout.write(u'Notification #{} for PM #{} and user "" deleted'.format(notification.pk,
                                                                                            topic.pk,
                                                                                            user))
