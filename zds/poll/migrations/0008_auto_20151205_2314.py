# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0007_auto_20151129_1919'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rangevote',
            unique_together=set([('user', 'choice', 'poll')]),
        ),
    ]
