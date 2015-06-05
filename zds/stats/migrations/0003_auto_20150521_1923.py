# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_auto_20150521_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='hash_code',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Hash code de la ligne de log'),
            preserve_default=True,
        ),
    ]
