# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0008_auto_20151205_2314'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='multiplevote',
            unique_together=set([('user', 'choice', 'poll')]),
        ),
    ]
