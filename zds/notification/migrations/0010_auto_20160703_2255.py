# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0009_newtopicsubscription'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('user', 'content_type', 'object_id')]),
        ),
    ]
