# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='group',
            field=models.ManyToManyField(to='auth.Group', verbose_name=b'Groupe autoris\xc3\xa9s (Aucun = public)', blank=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='tags',
            field=models.ManyToManyField(to='utils.Tag', db_index=True, verbose_name=b'Tags du forum', blank=True),
        ),
    ]
