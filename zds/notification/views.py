# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator

from zds import settings
from zds.mp.models import PrivateTopic
from zds.notification.models import Notification
from zds.utils.paginator import ZdSPagingListView


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
