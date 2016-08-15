# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from datetime import datetime
from django.contrib.auth.models import Group
from django.db.models import Q


class ProfileManager(models.Manager):
    """
    Custom profile manager.
    """

    def contactable_members(self):
        """
        Gets all members to whom you can send a private message and can respond.

        :return: All members contactable
        :rtype: QuerySet
        """
        excluded_groups = [Group.objects.get(name=settings.ZDS_APP['member']['bot_group'])]
        now = datetime.now()
        return super(ProfileManager, self).get_queryset()\
            .exclude(user__groups__in=excluded_groups)\
            .exclude(user__is_active=False)\
            .filter(Q(can_read=True) | Q(end_ban_read__lte=now))

    def all_members_ordered_by_date_joined(self):
        """
        Gets all members ordered by date joined.

        :return: All members ordered by date joined
        :rtype: QuerySet
        """
        return super(ProfileManager, self).get_queryset().order_by('-user__date_joined').all()
