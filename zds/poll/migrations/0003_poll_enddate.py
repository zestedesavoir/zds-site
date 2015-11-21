# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0002_auto_20151118_1930'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='enddate',
            field=models.DateTimeField(null=True, verbose_name=b'Date de fin', blank=True),
            preserve_default=True,
        ),
    ]
