from datetime import datetime, timedelta

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from zds.forum.models import Post, is_read as topic_is_read
from zds.mp.models import PrivateTopic
from zds.tutorialv2.models.database import Validation
from zds.notification.models import Notification, TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    NewTopicSubscription, NewPublicationSubscription
from zds.tutorialv2.models.database import ContentReaction, PublishableContent
from zds.utils import get_current_user
from zds.utils.models import Alert, HatRequest
from django.conf import settings
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.member.models import NewEmailProvider

register = template.Library()


@register.filter('is_read')
def is_read(topic):
    return topic_is_read(topic)


@register.filter('is_followed')
def is_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.does_exist(user, topic, is_active=True)


@register.filter('is_email_followed')
def is_email_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.does_exist(user, topic, is_active=True, by_email=True)


@register.filter('is_followed_for_new_topic')
def is_followed_for_new_topic(forum_or_tag):
    user = get_current_user()
    return NewTopicSubscription.objects.does_exist(user, forum_or_tag, is_active=True)


@register.filter('is_email_followed_for_new_topic')
def is_email_followed_for_new_topic(forum_or_tag):
    user = get_current_user()
    return NewTopicSubscription.objects.does_exist(user, forum_or_tag, is_active=True, by_email=True)


@register.filter('is_content_followed')
def is_content_followed(content):
    user = get_current_user()
    return user.is_authenticated() and ContentReactionAnswerSubscription.objects.does_exist(
        user, content, is_active=True)


@register.filter('is_content_email_followed')
def is_content_email_followed(content):
    user = get_current_user()
    return user.is_authenticated() and ContentReactionAnswerSubscription.objects.does_exist(
        user, content, is_active=True, by_email=True)


@register.filter('is_new_publication_followed')
def is_new_publication_followed(user_to_follow):
    user = get_current_user()
    return user.is_authenticated() and NewPublicationSubscription.objects.does_exist(
        user, user_to_follow, is_active=True)


@register.filter('is_new_publication_email_followed')
def is_new_publication_email_followed(user_to_follow):
    user = get_current_user()
    return user.is_authenticated() and NewPublicationSubscription.objects.does_exist(
        user, user_to_follow, is_active=True, by_email=True)


@register.filter('humane_delta')
def humane_delta(value):
    """
    Associating a key to a named period

    :param int value:
    :return: string
    """
    const = {
        1: _("Aujourd'hui"),
        2: _('Hier'),
        3: _('Les 7 derniers jours'),
        4: _('Les 30 derniers jours'),
        5: _('Plus ancien')
    }

    return const[value]


@register.filter('followed_topics')
def followed_topics(user):
    topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)[:10]
    # periods is a map associating a period (Today, Yesterday, Last n days)
    # with its corresponding number of days: (humane_delta index, number of days).
    # (3, 7) thus means that passing 3 to humane_delta would return "This week", for which
    # we'd like pubdate not to exceed 7 days.
    periods = ((1, 0), (2, 1), (3, 7), (4, 30), (5, 365))
    topics = {}
    for topic in topics_followed:
        for period in periods:
            if topic.last_message.pubdate.date() >= \
                    (datetime.now() - timedelta(days=int(period[1]), hours=0, minutes=0, seconds=0)).date():
                if period[0] in topics:
                    topics[period[0]].append(topic)
                else:
                    topics[period[0]] = [topic]
                break
    return topics


@register.filter('get_github_issue_url')
def get_github_issue_url(topic):
    if not topic.github_issue:
        return None
    else:
        return '{0}/{1}'.format(
            settings.ZDS_APP['site']['repository']['bugtracker'],
            topic.github_issue
        )


@register.filter('interventions_topics')
def interventions_topics(user):
    """
    Gets all notifications related to all notifiable models excluding private topics.
    """
    posts_unread = []

    private_topic = ContentType.objects.get_for_model(PrivateTopic)
    for notification in Notification.objects \
            .get_unread_notifications_of(user) \
            .exclude(subscription__content_type=private_topic):
        posts_unread.append({'pubdate': notification.pubdate,
                             'author': notification.sender,
                             'title': notification.title,
                             'url': notification.url})

    posts_unread.sort(key=lambda post: post['pubdate'].timetuple())

    return posts_unread


@register.filter('interventions_privatetopics')
def interventions_privatetopics(user):
    """
    Gets all unread messages in the user's inbox.
    """
    private_topic = ContentType.objects.get_for_model(PrivateTopic)
    notifications = list(Notification.objects
                         .get_unread_notifications_of(user)
                         .filter(subscription__content_type=private_topic)
                         .order_by('-pubdate'))
    return {'notifications': notifications, 'total': len(notifications)}


@register.filter(name='alerts_list')
def alerts_list(user):
    total = []
    alerts = Alert.objects.filter(solved=False).select_related('author', 'comment', 'content').order_by('-pubdate')[:10]
    nb_alerts = Alert.objects.filter(solved=False).count()
    for alert in alerts:
        if alert.scope == 'FORUM':
            post = Post.objects.select_related('topic').get(pk=alert.comment.pk)
            total.append({'title': post.topic.title,
                          'url': post.get_absolute_url(),
                          'pubdate': alert.pubdate,
                          'author': alert.author,
                          'text': alert.text})
        elif alert.scope == 'CONTENT':
            published = PublishableContent.objects.select_related('public_version').get(pk=alert.content.pk)
            total.append({'title': published.public_version.title if published.public_version else published.title,
                          'url': published.get_absolute_url_online() if published.public_version else '',
                          'pubdate': alert.pubdate,
                          'author': alert.author,
                          'text': alert.text})
        else:
            comment = ContentReaction.objects.select_related('related_content').get(pk=alert.comment.pk)
            total.append({'title': comment.related_content.title,
                          'url': comment.get_absolute_url(),
                          'pubdate': alert.pubdate,
                          'author': alert.author,
                          'text': alert.text})

    return {'alerts': total, 'nb_alerts': nb_alerts}


@register.filter(name='waiting_count')
def waiting_count(content_type):
    """
    Gets the number of waiting contents of the specified type (without validator).
    """
    if content_type not in TYPE_CHOICES_DICT:
        raise template.TemplateSyntaxError("'content_type' must be in 'zds.tutorialv2.models.TYPE_CHOICES_DICT'")

    return Validation.objects.filter(
        validator__isnull=True,
        status='PENDING',
        content__type=content_type).count()


@register.filter(name='new_providers_count')
def new_providers_count(user):
    return NewEmailProvider.objects.count()


@register.filter(name='requested_hats_count')
def requested_hats_count(user):
    return HatRequest.objects.filter(is_granted__isnull=True).count()
