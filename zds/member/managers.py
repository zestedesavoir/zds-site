# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models


class ProfileManager(models.Manager):
    """
    Custom profile manager.
    """
    def all_members_ordered_by_date_joined(self):
        return User.objects.order_by('-date_joined').all()
