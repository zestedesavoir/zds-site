# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models


class ProfileManager(models.Manager):
    """
    Custom profile manager.
    """

    def all_members_ordered_by_date_joined(self):
        return User.objects.order_by('-date_joined').all()

    def all_old_tutos_from_site_du_zero(self, profile):
        from models import get_info_old_tuto

        if profile.sdz_tutorial:
            olds = profile.sdz_tutorial.strip().split(":")
        else:
            olds = []

        oldtutos = []
        [oldtutos.append(get_info_old_tuto(old)) for old in olds]
        return oldtutos
