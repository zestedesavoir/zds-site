from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q


class ProfileManager(models.Manager):
    def contactable_members(self):
        """
        Gets all members to whom you can send a private message and can respond.

        :return: All contactable members
        :rtype: QuerySet
        """
        now = datetime.now()
        excluded_groups = [Group.objects.filter(name=settings.ZDS_APP["member"]["bot_group"]).first()]
        qs = (
            self.get_queryset()
            .exclude(user__is_active=False)
            .exclude(user__groups__in=excluded_groups)
            .filter(Q(can_read=True) | Q(end_ban_read__lte=now))
            .order_by("-user__date_joined")
            .select_related("user")
        )

        return qs
