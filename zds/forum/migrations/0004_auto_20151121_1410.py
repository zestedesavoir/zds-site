# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0003_auto_20150414_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='is_locked',
            field=models.BooleanField(default=False, db_index=True, verbose_name=b'Est verrouill\xc3\xa9'),
        ),
    ]
