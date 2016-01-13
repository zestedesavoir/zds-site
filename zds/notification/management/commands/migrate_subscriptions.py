# coding: utf-8
from django.core.management import BaseCommand
from django.db.models import F, Q
from zds.forum.models import TopicRead
from zds.member.models import Profile
from zds.mp.models import PrivateTopicRead, PrivateTopic
from zds.notification.models import TopicFollowed, TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    PrivateTopicAnswerSubscription
from zds.tutorialv2.models.models_database import ContentReaction, ContentRead


class Command(BaseCommand):
    help = 'Migrate old topic subscriptions and notifications for new models.'

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            # Forums.
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
                notification = TopicAnswerSubscription.objects\
                    .get_existing(profile, content_object, is_active=True).last_notification
                notification.pubdate = content.pubdate
                notification.save()

            # Private messages.
            topics_never_read = list(PrivateTopicRead.objects
                                     .filter(user=profile.user)
                                     .filter(privatepost=F('privatetopic__last_message')).all())

            tnrs = []
            for tnr in topics_never_read:
                tnrs.append(tnr.privatetopic.pk)

            private_topics_unread = PrivateTopic.objects \
                .filter(Q(author=profile.user) | Q(participants__in=[profile.user])) \
                .exclude(pk__in=tnrs) \
                .select_related("privatetopic") \
                .order_by("-pubdate") \
                .distinct()

            for private_topic_unread in private_topics_unread:
                answer = private_topic_unread.last_read_post(profile.user)
                if answer is None:
                    answer = private_topic_unread.get_last_answer()

                # Migrate subscriptions.
                subscription = PrivateTopicAnswerSubscription.objects.get_or_create_active(
                    profile=profile, content_object=private_topic_unread)

                # Migrate notifications.
                subscription.send_notification(content=answer, sender=answer.author.profile, send_email=False)
                notification = PrivateTopicAnswerSubscription.objects\
                    .get_existing(profile, private_topic_unread, is_active=True).last_notification
                notification.pubdate = answer.pubdate
                notification.save()

            # Contents.
            content_followed_pk = ContentReaction.objects\
                .filter(author=profile.user, related_content__public_version__isnull=False)\
                .values_list('related_content__pk', flat=True)

            content_to_read = ContentRead.objects\
                .select_related('note')\
                .select_related('note__author')\
                .select_related('content')\
                .select_related('note__related_content__public_version')\
                .filter(user=profile.user)\
                .exclude(note__pk=F('content__last_note__pk')).all()

            for content_read in content_to_read:
                content = content_read.content
                if content.pk not in content_followed_pk and profile.user not in content.authors.all():
                    continue
                reaction = content.first_unread_note(user=profile.user)
                if reaction is None:
                    reaction = content.first_note()
                if reaction is None:
                    continue

                # Migrate subscriptions.
                content_object = reaction.related_content
                subscription = ContentReactionAnswerSubscription.objects.get_or_create_active(
                    profile=profile, content_object=content_object)

                # Migrate notifications.
                subscription.send_notification(content=reaction, sender=reaction.author.profile)
                notification = ContentReactionAnswerSubscription.objects\
                    .get_existing(profile, content_object, is_active=True).last_notification
                notification.pubdate = reaction.pubdate
                notification.save()
