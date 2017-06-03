# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from zds import settings
from zds.mp.models import PrivateTopic
from zds.notification.models import Notification, Subscription
from zds.utils.paginator import ZdSPagingListView
from zds.forum.models import Post, Forum
from zds.tutorialv2.models.models_database import ContentReaction
from zds.forum.models import mark_read as mark_topic_read
from zds.tutorialv2.utils import mark_read as mark_content_read
from zds.utils.models import Tag


class NotificationList(ZdSPagingListView):
    """
    Displays the list of notifications.
    """

    context_object_name = 'notifications'
    paginate_by = settings.ZDS_APP['notification']['per_page']
    template_name = 'notification/followed.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(NotificationList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(PrivateTopic)
        return Notification.objects.get_notifications_of(self.request.user) \
            .exclude(subscription__content_type=content_type) \
            .order_by('is_read', '-pubdate') \
            .all()

    def get_context_data(self, **kwargs):
        user_content_type = ContentType.objects.get_for_model(User)
        forum_content_type = ContentType.objects.get_for_model(Forum)
        tag_content_type = ContentType.objects.get_for_model(Tag)

        context = super(NotificationList, self).get_context_data(**kwargs)
        context['followed_users'] = Subscription.objects \
            .filter(user=self.request.user, is_active=True, content_type=user_content_type) \
            .prefetch_related('content_object') \
            .prefetch_related('content_object__profile')
        context['followed_forums'] = Subscription.objects \
            .filter(user=self.request.user, is_active=True, content_type=forum_content_type) \
            .prefetch_related('content_object') \
            .prefetch_related('content_object__category')
        context['followed_tags'] = Subscription.objects \
            .filter(user=self.request.user, is_active=True, content_type=tag_content_type) \
            .prefetch_related('content_object')
        return context


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
    notifications = Notification.objects.get_unread_notifications_of(request.user) \
        .exclude(subscription__content_type=content_type) \

    for notification in notifications:
        if isinstance(notification.content_object, Post):
            mark_topic_read(notification.content_object.topic, request.user)
        if isinstance(notification.content_object, ContentReaction):
            mark_content_read(notification.content_object.related_content, request.user)

    notifications.update(is_read=True)

    messages.success(request, _(u'Vos notifications ont bien été marquées comme lues.'))

    return redirect(reverse('notification-list'))
