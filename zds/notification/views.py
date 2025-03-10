from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from zds.forum.models import Post
from zds.forum.models import mark_read as mark_topic_read
from zds.mp.models import PrivateTopic
from zds.notification.models import Notification
from zds.tutorialv2.models.database import ContentReaction
from zds.tutorialv2.utils import mark_read as mark_content_read
from zds.utils.paginator import ZdSPagingListView


class NotificationList(ZdSPagingListView):
    """
    Displays the list of notifications.
    """

    context_object_name = "notifications"
    paginate_by = settings.ZDS_APP["notification"]["per_page"]
    template_name = "notification/followed.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(PrivateTopic)
        return (
            Notification.objects.get_notifications_of(self.request.user)
            .exclude(subscription__content_type=content_type)
            .order_by("is_read", "-pubdate")
            .all()
        )


@require_POST
@login_required
def mark_notifications_as_read(request):
    """
    Mark the notifications of the current user as read.
    If a notification is linked to a comment, the topic
    or content associed is also marked as read.
    Note that notifications for private messages are not concerned.
    """

    content_type = ContentType.objects.get_for_model(PrivateTopic)
    notifications = Notification.objects.get_unread_notifications_of(request.user).exclude(
        subscription__content_type=content_type
    )
    for notification in notifications:
        if isinstance(notification.content_object, Post):
            mark_topic_read(notification.content_object.topic, request.user)
        if isinstance(notification.content_object, ContentReaction):
            mark_content_read(notification.content_object.related_content, request.user)

    notifications.update(is_read=True)

    messages.success(request, _("Vos notifications ont bien été marquées comme lues."))

    return redirect(reverse("notification:list"))
