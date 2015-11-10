# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_auto_20150410_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='is_locked',
            field=models.BooleanField(default=False, db_index=True, verbose_name=b'Est verrouill\xc3\xa9'),
            preserve_default=True,
        ),
    ]
