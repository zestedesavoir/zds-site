# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0007_auto_20160827_2035'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='topicread',
            unique_together=set([('topic', 'user')]),
        ),
    ]
