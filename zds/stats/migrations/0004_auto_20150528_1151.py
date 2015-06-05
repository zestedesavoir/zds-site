# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0003_auto_20150521_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='city',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Ville'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='log',
            name='country',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Pays'),
            preserve_default=True,
        ),
    ]
