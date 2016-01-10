# coding: utf-8

import time
from datetime import datetime, timedelta

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from zds.forum.models import Post, never_read as never_read_topic
from zds.member.models import Profile
from zds.mp.models import PrivateTopic
from zds.notification.models import Notification, TopicAnswerSubscription
from zds.tutorialv2.models.models_database import ContentReaction
from zds.utils import get_current_user
from zds.utils.models import Alert

register = template.Library()


@register.filter('is_read')
def is_read(topic):
    if never_read_topic(topic):
        return False
    else:
        return True


@register.filter('is_followed')
def is_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.get_existing(user.profile, topic, is_active=True) is not None


@register.filter('is_email_followed')
def is_email_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.get_existing(user.profile, topic, is_active=True, by_email=True) is not None


@register.filter('humane_delta')
def humane_delta(value):
    """
    Mapping between label day and key

    :param int value:
    :return: string
    """
    const = {
        1: _("Aujourd'hui"),
        2: _("Hier"),
        3: _("Les 7 derniers jours"),
        4: _("Les 30 derniers jours"),
        5: _("Plus ancien")
    }

    return const[value]


@register.filter('followed_topics')
def followed_topics(user):
    topics_followed = TopicAnswerSubscription.objects.filter(profile=user.profile,
                                                             content_type__model='topic',
                                                             is_active=True)\
        .order_by('-last_notification__pubdate')[:10]
    # This period is a map for link a moment (Today, yesterday, this week, this month, etc.) with
    # the number of days for which we can say we're still in the period
    # for exemple, the tuple (2, 1) means for the period "2" corresponding to "Yesterday" according
    # to humane_delta, means if your pubdate hasn't exceeded one day, we are always at "Yesterday"
    # Number is use for index for sort map easily
    periods = ((1, 0), (2, 1), (3, 7), (4, 30), (5, 360))
    topics = {}
    for topic_followed in topics_followed:
        for period in periods:
            if topic_followed.content_object.last_message.pubdate.date() \
                    >= (datetime.now() - timedelta(days=int(period[1]), hours=0, minutes=0, seconds=0)).date():
                if period[0] in topics:
                    topics[period[0]].append(topic_followed.content_object)
                else:
                    topics[period[0]] = [topic_followed.content_object]
                break
    return topics


def comp(dated_element1, dated_element2):
    version1 = int(time.mktime(dated_element1['pubdate'].timetuple()))
    version2 = int(time.mktime(dated_element2['pubdate'].timetuple()))
    if version1 > version2:
        return -1
    elif version1 < version2:
        return 1
    else:
        return 0


@register.filter('interventions_topics')
def interventions_topics(user):
    """
    Gets all notifications related to all notifiable models excluding private topics.
    """
    posts_unread = []

    private_topic = ContentType.objects.get_for_model(PrivateTopic)
    for notification in Notification.objects \
            .get_unread_notifications_of(Profile.objects.get(user=user)) \
            .exclude(subscription__content_type=private_topic):
        posts_unread.append({'pubdate': notification.pubdate,
                             'author': notification.sender.user,
                             'title': notification.title,
                             'url': notification.url})

    posts_unread.sort(cmp=comp)

    return posts_unread


@register.filter('interventions_privatetopics')
def interventions_privatetopics(user):
    """
    Gets all unread messages in the user's inbox.
    """
    private_topic = ContentType.objects.get_for_model(PrivateTopic)
    notifications = list(Notification.objects
                         .get_unread_notifications_of(Profile.objects.get(user=user))
                         .filter(subscription__content_type=private_topic)
                         .order_by('-pubdate'))
    return {'notifications': notifications, 'total': len(notifications)}


@register.filter(name='alerts_list')
def alerts_list(user):
    total = []
    alerts = Alert.objects.select_related('author', 'comment').all().order_by('-pubdate')[:10]
    nb_alerts = Alert.objects.count()
    for alert in alerts:
        if alert.scope == Alert.FORUM:
            post = Post.objects.select_related('topic').get(pk=alert.comment.pk)
            total.append({'title': post.topic.title,
                          'url': post.get_absolute_url(),
                          'pubdate': alert.pubdate,
                          'author': alert.author,
                          'text': alert.text})
        if alert.scope == Alert.CONTENT:
            note = ContentReaction.objects.select_related('related_content').get(pk=alert.comment.pk)
            total.append({'title': note.related_content.title,
                          'url': note.get_absolute_url(),
                          'pubdate': alert.pubdate,
                          'author': alert.author,
                          'text': alert.text})

    return {'alerts': total, 'nb_alerts': nb_alerts}
