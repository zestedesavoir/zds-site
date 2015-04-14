# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_auto_20150407_2258'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['position', 'title'], 'verbose_name': 'Cat\xe9gorie', 'verbose_name_plural': 'Cat\xe9gories'},
        ),
        migrations.AlterModelOptions(
            name='forum',
            options={'ordering': ['position_in_category', 'title'], 'verbose_name': 'Forum', 'verbose_name_plural': 'Forums'},
        ),
    ]
