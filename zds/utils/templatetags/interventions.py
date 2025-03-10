from datetime import datetime, timedelta

from django import template
from django.conf import settings
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from zds.member.models import NewEmailProvider
from zds.notification.models import (
    ContentReactionAnswerSubscription,
    NewPublicationSubscription,
    NewTopicSubscription,
    TopicAnswerSubscription,
)
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.tutorialv2.models.database import PickListOperation, PublishableContent, Validation
from zds.utils import get_current_user
from zds.utils.context_processor import get_repository_url
from zds.utils.models import HatRequest

register = template.Library()


@register.filter("is_followed")
def is_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.does_exist(user, topic, is_active=True)


@register.filter("is_email_followed")
def is_email_followed(topic):
    user = get_current_user()
    return TopicAnswerSubscription.objects.does_exist(user, topic, is_active=True, by_email=True)


@register.filter("is_followed_for_new_topic")
def is_followed_for_new_topic(forum_or_tag):
    user = get_current_user()
    return NewTopicSubscription.objects.does_exist(user, forum_or_tag, is_active=True)


@register.filter("is_email_followed_for_new_topic")
def is_email_followed_for_new_topic(forum_or_tag):
    user = get_current_user()
    return NewTopicSubscription.objects.does_exist(user, forum_or_tag, is_active=True, by_email=True)


@register.filter("is_content_followed")
def is_content_followed(content):
    user = get_current_user()
    return user.is_authenticated and ContentReactionAnswerSubscription.objects.does_exist(user, content, is_active=True)


@register.filter("is_content_email_followed")
def is_content_email_followed(content):
    user = get_current_user()
    return user.is_authenticated and ContentReactionAnswerSubscription.objects.does_exist(
        user, content, is_active=True, by_email=True
    )


@register.filter("is_new_publication_followed")
def is_new_publication_followed(user_to_follow):
    user = get_current_user()
    return user.is_authenticated and NewPublicationSubscription.objects.does_exist(user, user_to_follow, is_active=True)


@register.filter("is_new_publication_email_followed")
def is_new_publication_email_followed(user_to_follow):
    user = get_current_user()
    return user.is_authenticated and NewPublicationSubscription.objects.does_exist(
        user, user_to_follow, is_active=True, by_email=True
    )


@register.filter("humane_delta")
def humane_delta(value):
    """
    Associating a key to a named period

    :param int value:
    :return: string
    """
    const = {
        1: _("Aujourd'hui"),
        2: _("Hier"),
        3: _("Les 7 derniers jours"),
        4: _("Les 30 derniers jours"),
        5: _("Plus ancien"),
    }

    return const[value]


@register.filter("followed_topics")
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
            if (
                topic.last_message.pubdate.date()
                >= (datetime.now() - timedelta(days=int(period[1]), hours=0, minutes=0, seconds=0)).date()
            ):
                if period[0] in topics:
                    topics[period[0]].append(topic)
                else:
                    topics[period[0]] = [topic]
                break
    return topics


@register.filter("get_github_issue_url")
def get_github_issue_url(topic):
    if not topic.github_issue:
        return None
    else:
        if topic.github_repository_name:
            repository_name = topic.github_repository_name
        else:
            repository_name = settings.ZDS_APP["github_projects"]["default_repository"]
        bugtracker = get_repository_url(repository_name, "bugtracker")
        return f"{bugtracker}/{topic.github_issue}"


@register.filter(name="waiting_count")
def waiting_count(content_type):
    """
    Gets the number of waiting contents of the specified type (without validator).
    """
    if content_type not in TYPE_CHOICES_DICT:
        raise template.TemplateSyntaxError("'content_type' must be in 'zds.tutorialv2.models.TYPE_CHOICES_DICT'")

    if content_type == "OPINION":
        return (
            PublishableContent.objects.filter(type="OPINION", sha_public__isnull=False)
            .exclude(sha_picked=F("sha_public"))
            .exclude(pk__in=PickListOperation.objects.filter(is_effective=True).values_list("content__pk", flat=True))
            .count()
        )

    return Validation.objects.filter(validator__isnull=True, status="PENDING", content__type=content_type).count()


@register.filter(name="new_providers_count")
def new_providers_count(user):
    return NewEmailProvider.objects.count()


@register.filter(name="requested_hats_count")
def requested_hats_count(user):
    return HatRequest.objects.filter(is_granted__isnull=True).count()
