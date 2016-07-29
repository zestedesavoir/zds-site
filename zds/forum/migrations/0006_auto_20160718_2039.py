# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0005_auto_20151119_2224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='is_locked',
            field=models.BooleanField(default=False, verbose_name=b'Est verrouill\xc3\xa9'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='is_solved',
            field=models.BooleanField(default=False, verbose_name=b'Est r\xc3\xa9solu'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='is_sticky',
            field=models.BooleanField(default=False, verbose_name=b'Est en post-it'),
        ),
    ]
