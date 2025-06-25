import ipaddress
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q

from zds.member.utils import get_network_ip_filter, is_ipv6


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


class BlockedIPManager(models.Manager):
    def is_blocked(self, ip_address: str):
        """
        Checks if an IP address is blocked or not.
        """

        qs = self.get_queryset()
        if is_ipv6(ip_address):
            network_ip = get_network_ip_filter(ip_address)
            qs = qs.filter(
                Q(ip_address=ip_address) | (Q(is_network_address=True) & Q(ip_address__startswith=network_ip))
            )
        else:
            qs = qs.filter(ip_address=ip_address)
        return qs.count() > 0
