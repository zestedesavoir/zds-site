# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models


class ProfileManager(models.Manager):

    """
    Custom profile manager.
    """

    def all_members_ordered_by_date_joined(self):
        """
        Get all members ordered by date joined.

        :return: All members ordered by date joined
        :rtype: QuerySet
        """
        return User.objects.order_by('-date_joined').all()

    def all_old_tutos_from_site_du_zero(self, profile):
        """
        Get all tutorials from Site du Zéro for a member if exist.

        :param profile: the profile of a member
        :type profile: QuerySet
        :return: A list of tutorials from Site du Zéro for a member if exist.
        :rtype: list
        """
        from models import get_info_old_tuto

        if profile.sdz_tutorial:
            olds = profile.sdz_tutorial.strip().split(':')
        else:
            olds = []
        old_tutos =  [get_info_old_tuto(old) for old in olds]
        return old_tutos
