# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0002_auto_20160821_1539'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='type_vote',
        ),
        migrations.AddField(
            model_name='poll',
            name='multiple_vote',
            field=models.BooleanField(default=False, verbose_name='Vote multiple'),
        ),
    ]
