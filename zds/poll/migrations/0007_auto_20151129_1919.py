# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0006_auto_20151129_1910'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='unique_vote',
        ),
        migrations.AlterField(
            model_name='poll',
            name='type_vote',
            field=models.CharField(default=b'uniquevote', max_length=1, verbose_name=b'Type de vote', choices=[(b'u', b'Vote unique'), (b'm', b'Vote multiple'), (b'r', b'Vote par valeurs')]),
            preserve_default=True,
        ),
    ]
