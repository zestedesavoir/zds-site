# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0004_profile_allow_temp_visual_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='zds_smileys',
            field=models.BooleanField(default=True, verbose_name=b'Active le pack de smileys Clem'),
        ),
    ]
