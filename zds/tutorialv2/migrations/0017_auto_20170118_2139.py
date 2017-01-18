# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0016_auto_20161120_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='picked_date',
            field=models.DateTimeField(default=None, null=True, verbose_name='Date de mise en avant', db_index=True, blank=True),
        ),
    ]
