# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0003_poll_enddate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='anonymous_vote',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
