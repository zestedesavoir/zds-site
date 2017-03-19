# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0012_auto_20170204_2239'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='github_issue',
            field=models.PositiveIntegerField(null=True, verbose_name='Ticket GitHub', blank=True),
        ),
    ]
