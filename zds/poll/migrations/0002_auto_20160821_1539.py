# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='poll',
            old_name='enddate',
            new_name='end_date',
        ),
        migrations.AlterField(
            model_name='choice',
            name='poll',
            field=models.ForeignKey(related_name='choices', verbose_name='sondage', to='poll.Poll'),
        ),
    ]
