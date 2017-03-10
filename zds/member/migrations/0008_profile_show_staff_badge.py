# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from django.contrib.auth.models import User
from zds.member.models import Profile


def forwards_func(apps, schema_editor):
    # Check for each user if the staff badge should be displayed
    users = User.objects.select_related('profile').all()
    for user in users:
        try:
            user_profile = user.profile
            user_profile.show_staff_badge = user.has_perm('forum.change_post')
            user_profile.save()
        except Profile.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0007_auto_20161119_1836'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='show_staff_badge',
            field=models.BooleanField(default=False, verbose_name='Afficher le badge staff'),
        ),
        migrations.RunPython(forwards_func),
    ]
