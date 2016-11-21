# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0006_auto_20161119_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='is_hover_enabled',
            field=models.BooleanField(default=False, verbose_name=b'D\xc3\xa9roulement au survol ?'),
        ),
    ]
