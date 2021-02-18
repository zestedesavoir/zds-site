from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Post
from zds.mp.models import PrivateTopic
from zds.notification.models import Notification
from zds.tutorialv2.models.database import ContentReaction, PublishableContent
from zds.utils.models import Alert


def _notifications_to_list(notifications_query):
    query = notifications_query.select_related("sender__profile").order_by("-pubdate")[:10]

    return [{"pubdate": n.pubdate, "author": n.sender, "title": n.title, "url": n.url} for n in query]


def _get_alert_info(alert):
    if alert.scope == "FORUM":
        post = Post.objects.select_related("topic").get(pk=alert.comment.pk)
        return post.topic.title, post.get_absolute_url()
    elif alert.scope == "CONTENT":
        published = PublishableContent.objects.select_related("public_version").get(pk=alert.content.pk)
        title = published.public_version.title if published.public_version else published.title
        url = published.get_absolute_url_online() if published.public_version else ""
        return title, url
    elif alert.scope == "PROFILE":
        return _("Profil de {}").format(alert.profile.user.username), alert.profile.get_absolute_url() + "#alerts"
    else:
        comment = ContentReaction.objects.select_related("related_content").get(pk=alert.comment.pk)
        return (
            comment.related_content.title,
            comment.get_absolute_url(),
        )


def _alert_to_dict(alert):
    title, url = _get_alert_info(alert)
    return {"title": title, "url": url, "pubdate": alert.pubdate, "author": alert.author, "text": alert.text}


def _alerts_to_list(alerts_query):
    query = alerts_query.select_related("author", "comment", "content").order_by("-pubdate")[:10]

    return [_alert_to_dict(a) for a in query]


def get_header_notifications(user):
    if not user.is_authenticated:
        return None

    private_topic = ContentType.objects.get_for_model(PrivateTopic)

    notifications = Notification.objects.filter(subscription__user=user, is_read=False)

    general_notifications = notifications.exclude(subscription__content_type=private_topic)

    private_notifications = notifications.filter(subscription__content_type=private_topic)

    alerts = Alert.objects.filter(solved=False)

    return {
        "general_notifications": {
            "total": general_notifications.count(),
            "list": _notifications_to_list(general_notifications),
        },
        "private_topic_notifications": {
            "total": private_notifications.count(),
            "list": _notifications_to_list(private_notifications),
        },
        "alerts": user.has_perm("forum.change_post")
        and {
            "total": alerts.count(),
            "list": _alerts_to_list(alerts),
        },
    }
