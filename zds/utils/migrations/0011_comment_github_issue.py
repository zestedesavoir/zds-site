# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0010_auto_20170203_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='github_issue',
            field=models.IntegerField(null=True, verbose_name='Ticket GitHub', blank=True),
        ),
    ]
