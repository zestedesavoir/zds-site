# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class TutorialManager(models.Manager):
    """
    Custom tutorial manager.
    """

    def last_tutorials_of_a_member_loaded(self, author):
        my_tutorials = self.filter(sha_public__isnull=False) \
                          .filter(authors__in=[author]) \
                          .order_by("-pubdate") \
                          .all()[:settings.ZDS_APP['tutorial']['home_number']]
        my_tuto_versions = []
        for my_tutorial in my_tutorials:
            mandata = my_tutorial.load_json_for_public()
            my_tutorial.load_dic(mandata)
            my_tuto_versions.append(mandata)
        return my_tuto_versions
