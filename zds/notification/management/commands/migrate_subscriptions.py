# coding: utf-8
from django.core.management import BaseCommand
from django.db.models import F

from zds.forum.models import TopicRead
from zds.member.models import Profile
from zds.notification.models import TopicFollowed, TopicAnswerSubscription


class Command(BaseCommand):
    help = 'Migrate old topic subscriptions and notifications for new models.'

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            topics_followed = TopicFollowed.objects.filter(user=profile.user).values("topic").distinct().all()
            topics_never_read = TopicRead.objects\
                .filter(user=profile.user)\
                .filter(topic__in=topics_followed)\
                .select_related("topic")\
                .exclude(post=F('topic__last_message')).all()

            for topic_never_read in topics_never_read:
                content = topic_never_read.topic.first_unread_post(profile.user)
                if content is None:
                    content = topic_never_read.topic.last_message

                # Migrate subscriptions.
                content_object = topic_never_read.topic
                subscription = TopicAnswerSubscription.objects.get_or_create_active(
                    profile=profile, content_object=content_object)

                # Migrate notifications.
                subscription.send_notification(content=content, sender=content.author.profile)
